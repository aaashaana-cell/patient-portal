options(stringsAsFactors = FALSE)

base <- '/Users/shanuakshah/Downloads/files (3)/pre-post 16_02_2026'
data_dir <- file.path(base, '04_datasets_mappings')
out_dir <- file.path(base, '01_interpretation_pack')

resp <- read.csv(file.path(data_dir, 'rerun2026_responder_362_standardized.csv'), check.names = FALSE)
non512 <- read.csv(file.path(data_dir, 'rerun2026_nonresponder_all_standardized.csv'), check.names = FALSE)
non453 <- read.csv(file.path(data_dir, 'rerun2026_nonresponder_oldlogic453_standardized.csv'), check.names = FALSE)
state_map <- read.csv(file.path(data_dir, 'state_code_mapping_full_from_sav.csv'), check.names = FALSE)

trimv <- function(x) {
  x <- as.character(x)
  x <- trimws(x)
  x[x == 'NA'] <- ''
  x
}

is_blank <- function(x) {
  x <- trimv(x)
  is.na(x) | x == ''
}

to_num <- function(x) suppressWarnings(as.numeric(trimv(x)))

map_state <- function(code) {
  code <- trimv(code)
  out <- rep(NA_character_, length(code))
  idx <- match(code, as.character(state_map$state_code))
  ok <- !is.na(idx)
  out[ok] <- as.character(state_map$state_name[idx[ok]])
  out
}

mk_binary <- function(x) as.integer(!is_blank(x))

prepare_df <- function(non_df, def_name) {
  r <- resp
  n <- non_df
  r$group <- 'Responder'
  n$group <- 'NonResponder'
  d <- rbind(r, n)
  d$definition <- def_name
  d$non_response <- ifelse(d$group == 'NonResponder', 1, 0)

  d$age <- to_num(d$q0005)
  g <- trimv(d$q0006)
  d$gender <- ifelse(g == '1', 'Male', ifelse(g == '2', 'Female', NA))
  d$gender <- factor(d$gender, levels = c('Female', 'Male'))

  csl <- trimv(d$q0012)
  d$caseload <- ifelse(csl == '1', '<10', ifelse(csl == '2', '11-20', ifelse(csl == '3', '21-30', ifelse(csl == '4', '>30', NA))))
  d$caseload <- factor(d$caseload, levels = c('<10', '11-20', '21-30', '>30'))

  d$training_skill <- mk_binary(d$q0010_0003)
  d$bar_dv <- mk_binary(d$q0013_0002)
  d$bar_ipv <- mk_binary(d$q0013_0003)
  d$bar_sv <- mk_binary(d$q0013_0004)
  d$bar_helpless <- mk_binary(d$q0013_0007)
  d$bar_nochange <- mk_binary(d$q0013_0009)

  d$state_code <- trimv(d$q0007)
  d$state_name <- map_state(d$state_code)

  # states with >=10 total responses in this definition retained as individual levels, others collapsed
  st <- table(d$state_name)
  keep <- names(st[st >= 10])
  d$state_bucket <- ifelse(is.na(d$state_name), NA, ifelse(d$state_name %in% keep, d$state_name, 'OtherSmall'))
  d$state_bucket <- factor(d$state_bucket)

  d
}

extract_glm <- function(fit, definition, model_name, n_used) {
  s <- summary(fit)$coefficients
  terms <- rownames(s)
  out <- data.frame(
    definition = definition,
    model = model_name,
    n_used = n_used,
    term = terms,
    beta = s[, 1],
    se = s[, 2],
    z = s[, 3],
    p_value = s[, 4],
    stringsAsFactors = FALSE
  )
  out <- out[out$term != '(Intercept)', ]
  out$OR <- exp(out$beta)
  out$CI_low <- exp(out$beta - 1.96 * out$se)
  out$CI_high <- exp(out$beta + 1.96 * out$se)
  out$significant <- ifelse(out$p_value < 0.05, 'Yes', 'No')
  out
}

run_models <- function(df, definition) {
  vars_base <- c('non_response', 'age', 'gender', 'caseload', 'training_skill', 'bar_dv', 'bar_ipv', 'bar_sv', 'bar_helpless', 'bar_nochange')
  vars_full <- c(vars_base, 'state_bucket')

  d1 <- df[complete.cases(df[, vars_base]), ]
  d2 <- df[complete.cases(df[, vars_full]), ]

  m1 <- glm(non_response ~ age + gender + caseload + training_skill + bar_dv + bar_ipv + bar_sv + bar_helpless + bar_nochange,
            family = binomial(), data = d1)
  m2 <- glm(non_response ~ age + gender + caseload + training_skill + bar_dv + bar_ipv + bar_sv + bar_helpless + bar_nochange + state_bucket,
            family = binomial(), data = d2, control = list(maxit = 100))

  r1 <- extract_glm(m1, definition, 'Adjusted_NoState', nrow(d1))
  r2 <- extract_glm(m2, definition, 'Adjusted_WithStateBucket', nrow(d2))
  rbind(r1, r2)
}

# effect size helpers
cohen_d_ci <- function(x1, x0) {
  n1 <- length(x1); n0 <- length(x0)
  m1 <- mean(x1); m0 <- mean(x0)
  s1 <- sd(x1); s0 <- sd(x0)
  sp <- sqrt(((n1 - 1) * s1^2 + (n0 - 1) * s0^2) / (n1 + n0 - 2))
  d <- (m1 - m0) / sp
  se_d <- sqrt((n1 + n0) / (n1 * n0) + (d^2) / (2 * (n1 + n0 - 2)))
  c(d = d, d_low = d - 1.96 * se_d, d_high = d + 1.96 * se_d,
    mean_diff = m1 - m0)
}

or_ci_from_2x2 <- function(tab, non_vs_resp = TRUE) {
  # tab rows: Responder, NonResponder; cols: No, Yes
  a <- tab[1, 2]; b <- tab[1, 1]; c <- tab[2, 2]; d <- tab[2, 1]
  if (any(c(a, b, c, d) == 0)) {
    a <- a + 0.5; b <- b + 0.5; c <- c + 0.5; d <- d + 0.5
  }
  if (non_vs_resp) {
    or <- (c / d) / (a / b)
    se <- sqrt(1 / c + 1 / d + 1 / a + 1 / b)
    log_or <- log(or)
  } else {
    or <- (a / b) / (c / d)
    se <- sqrt(1 / c + 1 / d + 1 / a + 1 / b)
    log_or <- log(or)
  }
  c(or = or, low = exp(log_or - 1.96 * se), high = exp(log_or + 1.96 * se))
}

cat_test <- function(tab) {
  test_name <- 'Chi-square test'
  p <- NA_real_
  if (all(dim(tab) == c(2, 2))) {
    expv <- suppressWarnings(chisq.test(tab, correct = FALSE)$expected)
    if (any(expv < 5)) {
      test_name <- 'Fisher exact test'
      p <- fisher.test(tab)$p.value
    } else {
      p <- suppressWarnings(chisq.test(tab, correct = FALSE)$p.value)
    }
  } else {
    base <- suppressWarnings(chisq.test(tab))
    if (any(base$expected < 5)) {
      test_name <- 'Chi-square test (simulated p)'
      p <- suppressWarnings(chisq.test(tab, simulate.p.value = TRUE, B = 20000)$p.value)
    } else {
      p <- base$p.value
    }
  }
  list(test = test_name, p = p)
}

cramers_v <- function(tab) {
  cs <- suppressWarnings(chisq.test(tab, correct = FALSE)$statistic)
  cs <- as.numeric(cs)
  n <- sum(tab)
  k <- min(nrow(tab) - 1, ncol(tab) - 1)
  if (n == 0 || k <= 0) return(NA_real_)
  sqrt(cs / (n * k))
}

bootstrap_v <- function(df, var, B = 1000) {
  vals <- c()
  n <- nrow(df)
  for (i in seq_len(B)) {
    idx <- sample.int(n, n, replace = TRUE)
    dd <- df[idx, ]
    dd <- dd[!is.na(dd[[var]]) & dd[[var]] != '', ]
    if (nrow(dd) < 10) next
    tab <- table(dd$group, dd[[var]])
    if (nrow(tab) < 2 || ncol(tab) < 2) next
    vals <- c(vals, cramers_v(tab))
  }
  if (length(vals) < 50) return(c(low = NA_real_, high = NA_real_))
  q <- quantile(vals, probs = c(0.025, 0.975), na.rm = TRUE)
  c(low = as.numeric(q[1]), high = as.numeric(q[2]))
}

binary_effect <- function(df, var, label, definition) {
  x <- mk_binary(df[[var]])
  tab <- table(df$group, x)
  # enforce columns 0/1
  for (lv in c('0', '1')) if (!(lv %in% colnames(tab))) tab <- cbind(tab, setNames(rep(0, nrow(tab)), lv))
  tab <- tab[, c('0', '1')]
  tst <- cat_test(tab)
  orv <- or_ci_from_2x2(tab, non_vs_resp = TRUE)
  data.frame(
    definition = definition,
    variable = var,
    label = label,
    metric = 'OR_nonresponse_vs_response',
    effect = as.numeric(orv['or']),
    ci_low = as.numeric(orv['low']),
    ci_high = as.numeric(orv['high']),
    test = tst$test,
    p_value = tst$p,
    stringsAsFactors = FALSE
  )
}

age_effect <- function(df, definition) {
  x1 <- df$age[df$group == 'Responder' & !is.na(df$age)]
  x0 <- df$age[df$group == 'NonResponder' & !is.na(df$age)]
  tt <- t.test(x1, x0)
  dd <- cohen_d_ci(x1, x0)
  r1 <- data.frame(
    definition = definition,
    variable = 'q0005',
    label = 'Age',
    metric = 'MeanDiff_Responder_minus_NonResponder',
    effect = unname(dd['mean_diff']),
    ci_low = tt$conf.int[1],
    ci_high = tt$conf.int[2],
    test = 'Welch t-test',
    p_value = tt$p.value,
    stringsAsFactors = FALSE
  )
  r2 <- data.frame(
    definition = definition,
    variable = 'q0005',
    label = 'Age',
    metric = 'Cohens_d_Responder_minus_NonResponder',
    effect = unname(dd['d']),
    ci_low = unname(dd['d_low']),
    ci_high = unname(dd['d_high']),
    test = 'Standardized mean difference',
    p_value = tt$p.value,
    stringsAsFactors = FALSE
  )
  rbind(r1, r2)
}

multi_effect <- function(df, var, label, definition) {
  dd <- df[!is.na(df[[var]]) & df[[var]] != '', ]
  tab <- table(dd$group, dd[[var]])
  tst <- cat_test(tab)
  v <- cramers_v(tab)
  ci <- bootstrap_v(dd[, c('group', var)], var, B = 1000)
  data.frame(
    definition = definition,
    variable = var,
    label = label,
    metric = 'Cramers_V',
    effect = v,
    ci_low = ci['low'],
    ci_high = ci['high'],
    test = tst$test,
    p_value = tst$p,
    stringsAsFactors = FALSE
  )
}

state_stability <- function(df, definition) {
  d <- df[!is.na(df$state_name) & df$state_name != '', c('group', 'state_name')]
  tab_all <- table(d$group, d$state_name)
  tst_all <- cat_test(tab_all)
  v_all <- cramers_v(tab_all)
  ci_all <- bootstrap_v(d, 'state_name', B = 1000)

  totals <- colSums(tab_all)
  keep <- names(totals[totals >= 10])
  d_thr <- d[d$state_name %in% keep, ]
  tab_thr <- table(d_thr$group, d_thr$state_name)
  tst_thr <- cat_test(tab_thr)
  v_thr <- cramers_v(tab_thr)
  ci_thr <- bootstrap_v(d_thr, 'state_name', B = 1000)

  # completion tables
  make_comp <- function(tab) {
    st <- data.frame(state_name = colnames(tab),
                     n_responder = as.integer(tab['Responder', ]),
                     n_nonresponder = as.integer(tab['NonResponder', ]),
                     stringsAsFactors = FALSE)
    st$total_n <- st$n_responder + st$n_nonresponder
    st$completion_rate <- st$n_responder / st$total_n
    st$completion_rate_pct <- sprintf('%.1f%%', 100 * st$completion_rate)
    st[order(-st$n_responder, -st$total_n), ]
  }

  comp_all <- make_comp(tab_all)
  comp_thr <- make_comp(tab_thr)

  top_all <- head(comp_all, 10)
  top_thr <- head(comp_thr, 10)
  zero_all <- comp_all[comp_all$n_responder == 0, ]
  zero_thr <- comp_thr[comp_thr$n_responder == 0, ]

  high_thr <- comp_thr[comp_thr$completion_rate == max(comp_thr$completion_rate, na.rm = TRUE), ]
  low_thr <- comp_thr[comp_thr$completion_rate == min(comp_thr$completion_rate, na.rm = TRUE), ]

  summ <- data.frame(
    definition = definition,
    metric = c('all_states_n', 'threshold_states_n_ge_10', 'dropped_states_lt_10',
               'all_states_test', 'all_states_p', 'all_states_cramers_v', 'all_states_v_ci_low', 'all_states_v_ci_high',
               'threshold_test', 'threshold_p', 'threshold_cramers_v', 'threshold_v_ci_low', 'threshold_v_ci_high'),
    value = c(ncol(tab_all), ncol(tab_thr), ncol(tab_all) - ncol(tab_thr),
              tst_all$test, format(tst_all$p, digits = 4), format(v_all, digits = 4), format(ci_all['low'], digits = 4), format(ci_all['high'], digits = 4),
              tst_thr$test, format(tst_thr$p, digits = 4), format(v_thr, digits = 4), format(ci_thr['low'], digits = 4), format(ci_thr['high'], digits = 4)),
    stringsAsFactors = FALSE
  )

  list(summary = summ,
       top_all = top_all,
       top_thr = top_thr,
       zero_all = zero_all,
       zero_thr = zero_thr,
       high_thr = high_thr,
       low_thr = low_thr,
       effect_all = data.frame(definition = definition, variable = 'q0007_state_all', label = 'State (all states)',
                               metric = 'Cramers_V', effect = v_all, ci_low = ci_all['low'], ci_high = ci_all['high'],
                               test = tst_all$test, p_value = tst_all$p, stringsAsFactors = FALSE),
       effect_thr = data.frame(definition = definition, variable = 'q0007_state_threshold_ge10', label = 'State (states with n>=10)',
                               metric = 'Cramers_V', effect = v_thr, ci_low = ci_thr['low'], ci_high = ci_thr['high'],
                               test = tst_thr$test, p_value = tst_thr$p, stringsAsFactors = FALSE)
  )
}

run_suite <- function(non_df, definition) {
  d <- prepare_df(non_df, definition)

  # 1) adjusted models
  model_tbl <- run_models(d, definition)

  # 2) effect sizes + CI
  eff <- age_effect(d, definition)
  eff <- rbind(eff,
               binary_effect(d, 'q0010_0003', 'Skill-based training workshop (q0010_0003)', definition),
               binary_effect(d, 'q0013_0002', 'Barrier: not trained for DV (q0013_0002)', definition),
               binary_effect(d, 'q0013_0003', 'Barrier: not trained for IPV (q0013_0003)', definition),
               binary_effect(d, 'q0013_0004', 'Barrier: not trained for sexual violence (q0013_0004)', definition),
               binary_effect(d, 'q0013_0007', 'Barrier: feel helpless (q0013_0007)', definition),
               binary_effect(d, 'q0013_0009', 'Barrier: unlikely to change (q0013_0009)', definition),
               multi_effect(d, 'caseload', 'GBV caseload per week', definition),
               multi_effect(d, 'gender', 'Gender', definition)
  )

  # 5) state stability
  st <- state_stability(d, definition)
  eff <- rbind(eff, st$effect_all, st$effect_thr)

  list(data = d, models = model_tbl, effects = eff, state = st)
}

res512 <- run_suite(non512, '362_vs_512')
res453 <- run_suite(non453, '362_vs_453')

# Write outputs
write.csv(rbind(res512$models, res453$models), file.path(out_dir, 'ADVANCED_01_AdjustedLogistic_Models.csv'), row.names = FALSE)
write.csv(rbind(res512$effects, res453$effects), file.path(out_dir, 'ADVANCED_02_EffectSizes_CI.csv'), row.names = FALSE)

write.csv(res512$state$summary, file.path(out_dir, 'ADVANCED_03_StateStability_362vs512_Summary.csv'), row.names = FALSE)
write.csv(res453$state$summary, file.path(out_dir, 'ADVANCED_03_StateStability_362vs453_Summary.csv'), row.names = FALSE)
write.csv(res512$state$top_all, file.path(out_dir, 'ADVANCED_03_StateStability_362vs512_TopStates_All.csv'), row.names = FALSE)
write.csv(res512$state$top_thr, file.path(out_dir, 'ADVANCED_03_StateStability_362vs512_TopStates_ThresholdGE10.csv'), row.names = FALSE)
write.csv(res453$state$top_all, file.path(out_dir, 'ADVANCED_03_StateStability_362vs453_TopStates_All.csv'), row.names = FALSE)
write.csv(res453$state$top_thr, file.path(out_dir, 'ADVANCED_03_StateStability_362vs453_TopStates_ThresholdGE10.csv'), row.names = FALSE)

# sensitivity table across definitions
key <- c('q0005|MeanDiff_Responder_minus_NonResponder',
         'q0005|Cohens_d_Responder_minus_NonResponder',
         'caseload|Cramers_V',
         'q0010_0003|OR_nonresponse_vs_response',
         'q0013_0002|OR_nonresponse_vs_response',
         'q0013_0003|OR_nonresponse_vs_response',
         'q0013_0004|OR_nonresponse_vs_response',
         'q0013_0007|OR_nonresponse_vs_response',
         'q0013_0009|OR_nonresponse_vs_response',
         'q0007_state_all|Cramers_V',
         'q0007_state_threshold_ge10|Cramers_V')

mk_key <- function(df) paste(df$variable, df$metric, sep='|')

e512 <- res512$effects; e453 <- res453$effects
e512$key <- mk_key(e512); e453$key <- mk_key(e453)

sens <- data.frame()
for (k in key) {
  a <- e512[e512$key == k, ]
  b <- e453[e453$key == k, ]
  if (nrow(a) == 0 || nrow(b) == 0) next
  row <- data.frame(
    variable = a$variable[1],
    label = a$label[1],
    metric = a$metric[1],
    all512_effect = a$effect[1],
    all512_ci = sprintf('[%.3f, %.3f]', a$ci_low[1], a$ci_high[1]),
    all512_p = a$p_value[1],
    old453_effect = b$effect[1],
    old453_ci = sprintf('[%.3f, %.3f]', b$ci_low[1], b$ci_high[1]),
    old453_p = b$p_value[1],
    significance_consistency = ifelse((a$p_value[1] < 0.05) == (b$p_value[1] < 0.05), 'Same', 'Different'),
    stringsAsFactors = FALSE
  )
  sens <- rbind(sens, row)
}
write.csv(sens, file.path(out_dir, 'ADVANCED_04_Sensitivity_AcrossDefinitions.csv'), row.names = FALSE)

# HTML summary
fmt_p <- function(p) ifelse(is.na(p), 'NA', ifelse(p < 0.001, '<0.001', sprintf('%.4f', p)))

sig_models <- rbind(res512$models, res453$models)
sig_models <- sig_models[sig_models$p_value < 0.05, c('definition', 'model', 'term', 'OR', 'CI_low', 'CI_high', 'p_value')]
if (nrow(sig_models) > 0) {
  sig_models$OR_CI <- sprintf('%.2f [%.2f, %.2f]', sig_models$OR, sig_models$CI_low, sig_models$CI_high)
  sig_models$p_value <- sapply(sig_models$p_value, fmt_p)
}

css <- '<style>body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Arial,sans-serif;margin:24px;background:#f7fafc;color:#12263a}h1{margin:0 0 10px}h2{margin:22px 0 8px}table{border-collapse:collapse;width:100%;background:#fff;border:1px solid #d9e2ec;font-size:12px}th,td{border:1px solid #e4ebf2;padding:6px 8px;text-align:left}th{background:#f0f4f8}.note{background:#fff8e1;border:1px solid #f0d17a;padding:10px;border-radius:8px;margin:10px 0}</style>'

mk_table <- function(df, title) {
  if (nrow(df) == 0) return(paste0('<h3>', title, '</h3><p><em>No rows.</em></p>'))
  cols <- names(df)
  h <- paste0('<h3>', title, '</h3><table><thead><tr>', paste(sprintf('<th>%s</th>', cols), collapse=''), '</tr></thead><tbody>')
  for (i in seq_len(nrow(df))) {
    h <- paste0(h, '<tr>', paste(sprintf('<td>%s</td>', as.character(df[i, cols])), collapse=''), '</tr>')
  }
  paste0(h, '</tbody></table>')
}

html <- c(
  '<!doctype html><html><head><meta charset="utf-8"><title>Advanced Analytics (1,2,5,Sensitivity)</title>',
  css,
  '</head><body>',
  '<h1>Advanced Analytics: Requested Items 1, 2, 5, and Sensitivity</h1>',
  '<div class="note">Includes: adjusted logistic models, effect sizes with 95% CIs, state stability checks (all states vs n>=10 threshold), and side-by-side sensitivity across non-responder definitions.</div>',
  mk_table(sig_models, 'A. Significant predictors from adjusted logistic models (OR and 95% CI)'),
  mk_table(res512$state$summary, 'B1. State stability summary (362 vs 512)'),
  mk_table(res453$state$summary, 'B2. State stability summary (362 vs 453)'),
  mk_table(sens, 'C. Sensitivity table across definitions'),
  '</body></html>'
)
writeLines(html, file.path(out_dir, 'ADVANCED_Analytics_Summary_1_2_5_Sensitivity.html'))

cat('Done\n')
