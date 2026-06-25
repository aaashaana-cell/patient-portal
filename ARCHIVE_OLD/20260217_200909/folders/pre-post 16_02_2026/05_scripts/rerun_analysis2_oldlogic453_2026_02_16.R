options(stringsAsFactors = FALSE)

out_dir <- '/Users/shanuakshah/Downloads/files (3)/pre-post 16_02_2026'
resp <- read.csv(file.path(out_dir, 'rerun2026_responder_362_standardized.csv'), check.names = FALSE)
non <- read.csv(file.path(out_dir, 'rerun2026_nonresponder_oldlogic453_standardized.csv'), check.names = FALSE)

trim_vec <- function(x) {
  x <- as.character(x)
  x <- trimws(x)
  x[x == 'NA'] <- ''
  x
}

is_missing <- function(x) {
  x <- trim_vec(x)
  is.na(x) | x == ''
}

to_num <- function(x) suppressWarnings(as.numeric(trim_vec(x)))

fmt_n_pct <- function(n, d) {
  if (is.na(d) || d == 0) return('0 (0.0%)')
  sprintf('%d (%.1f%%)', n, 100 * n / d)
}

p_fmt <- function(p) {
  if (is.na(p)) return('NA')
  if (p < 0.001) return('<0.001')
  sprintf('%.4f', p)
}

interpret_p <- function(p, direction = NULL) {
  if (is.na(p)) return('Test not run (insufficient data).')
  if (p < 0.05) {
    if (!is.null(direction) && nzchar(direction)) return(direction)
    return('Significant group difference (p<0.05).')
  }
  'No statistically significant group difference (p>=0.05).'
}

escape_html <- function(x) {
  x <- as.character(x)
  x <- gsub('&', '&amp;', x, fixed = TRUE)
  x <- gsub('<', '&lt;', x, fixed = TRUE)
  x <- gsub('>', '&gt;', x, fixed = TRUE)
  x
}

df_to_html <- function(df, title = NULL) {
  if (nrow(df) == 0) return('<p><em>No rows.</em></p>')
  html <- ''
  if (!is.null(title)) html <- paste0(html, '<h3>', escape_html(title), '</h3>')
  html <- paste0(html, '<table border="1" cellspacing="0" cellpadding="4" style="border-collapse:collapse; font-size:11px;">')
  html <- paste0(html, '<tr>')
  for (nm in names(df)) html <- paste0(html, '<th>', escape_html(nm), '</th>')
  html <- paste0(html, '</tr>')
  for (i in seq_len(nrow(df))) {
    html <- paste0(html, '<tr>')
    for (nm in names(df)) html <- paste0(html, '<td>', escape_html(df[i, nm]), '</td>')
    html <- paste0(html, '</tr>')
  }
  paste0(html, '</table>')
}

labels_map <- list(
  q0006 = c('1' = 'Male', '2' = 'Female'),
  q0008 = c('1' = "Bachelor's", '2' = "Master's"),
  q0009 = c('1' = '<3 years', '2' = '3-6 years', '3' = '>6 years'),
  q0011 = c('1' = 'None', '2' = '1-3', '3' = '>3'),
  q0012 = c('1' = '<10', '2' = '11-20', '3' = '21-30', '4' = '>30'),
  q0015 = c('1' = 'Very low', '2' = 'Low', '3' = 'Average', '4' = 'High', '5' = 'Very high'),
  q0016 = c('1' = 'Very low', '2' = 'Low', '3' = 'Average', '4' = 'High', '5' = 'Very high'),
  q0017 = c('1' = 'Very low', '2' = 'Low', '3' = 'Average', '4' = 'High', '5' = 'Very high')
)

var_name_map <- c(
  q0005 = 'Age',
  q0006 = 'Gender',
  q0008 = 'Education',
  q0009 = 'Years of experience',
  q0011 = 'Post-joining GBV training programs attended',
  q0012 = 'GBV caseload per week',
  q0007 = 'State',
  q0015 = 'Knowledge of GBV/IPV',
  q0016 = 'Awareness of local resources',
  q0017 = 'Awareness of mental health issues related to GBV'
)

checkbox_labels_training <- c(
  q0010_0001 = 'No formal training',
  q0010_0002 = 'Attended lectures/webinars on GBV',
  q0010_0003 = 'Skill-based training workshops on GBV',
  q0010_0004 = 'Counselling/certificate course on GBV',
  q0010_0005 = 'Diploma/degree in GBV counselling',
  q0010_other = 'Other formal training (free-text entered)'
)

checkbox_labels_barriers <- c(
  q0013_0001 = 'Not enough time to assess women',
  q0013_0002 = 'Not adequately trained to assess DV',
  q0013_0003 = 'Not adequately trained to assess IPV',
  q0013_0004 = 'Not adequately trained to assess sexual violence',
  q0013_0005 = 'Afraid of offending/upsetting women',
  q0013_0006 = 'Privacy barrier for interviewing alone',
  q0013_0007 = 'Feel helpless assisting women',
  q0013_0008 = 'Not aware of referral resources',
  q0013_0009 = 'Belief situation unlikely to change',
  q0013_0010 = 'Concerns about legal issues',
  q0013_0011 = 'Unsure when perpetrator is present',
  q0013_0012 = 'Other barrier option selected'
)

confidence_labels <- c(
  q0014_0001 = 'Q14-1 Emotional violence questions',
  q0014_0002 = 'Q14-2 Physical violence questions',
  q0014_0003 = 'Q14-3 Sexual violence questions',
  q0014_0004 = 'Q14-4 Counselling IPV',
  q0014_0005 = 'Q14-5 Psychological First Aid',
  q0014_0006 = 'Q14-6 Safety planning',
  q0014_0007 = 'Q14-7 Child sexual abuse cases',
  q0014_0008 = 'Q14-8 Pregnant/postpartum GBV',
  q0014_0009 = 'Q14-9 Elderly women GBV',
  q0014_0010 = 'Q14-10 Anxiety/depression issues',
  q0014_0011 = 'Q14-11 Severe mental illness signs',
  q0014_0012 = 'Q14-12 Self-harm/suicidal disclosure',
  q0014_0013 = 'Q14-13 Referring to mental health professional',
  q0014_0014 = 'Q14-14 Handling husbands/perpetrator conversations',
  q0014_0015 = 'Q14-15 Tele-counselling',
  q0014_0016 = 'Q14-16 Ethical dilemmas/confidentiality'
)

numeric_compare <- function(var, label) {
  x_r <- to_num(resp[[var]]); x_n <- to_num(non[[var]])
  x_r <- x_r[!is.na(x_r)]; x_n <- x_n[!is.na(x_n)]
  p <- NA
  if (length(x_r) >= 2 && length(x_n) >= 2) p <- tryCatch(t.test(x_r, x_n)$p.value, error = function(e) NA)
  direction <- NULL
  if (!is.na(p) && p < 0.05) {
    direction <- ifelse(mean(x_r) > mean(x_n), sprintf('Responders had higher %s (p<0.05).', label), sprintf('Responders had lower %s (p<0.05).', label))
  }
  data.frame(variable = var, label = label,
             responder_n = length(x_r), responder_mean = ifelse(length(x_r) > 0, sprintf('%.2f', mean(x_r)), 'NA'), responder_sd = ifelse(length(x_r) > 1, sprintf('%.2f', sd(x_r)), 'NA'),
             nonresponder_n = length(x_n), nonresponder_mean = ifelse(length(x_n) > 0, sprintf('%.2f', mean(x_n)), 'NA'), nonresponder_sd = ifelse(length(x_n) > 1, sprintf('%.2f', sd(x_n)), 'NA'),
             test = 'Welch t-test', p_value = p_fmt(p), interpretation = interpret_p(p, direction), stringsAsFactors = FALSE)
}

categorical_compare <- function(var, label, labels = NULL) {
  v_r <- trim_vec(resp[[var]]); v_n <- trim_vec(non[[var]])
  keep_r <- !is.na(v_r) & v_r != ''; keep_n <- !is.na(v_n) & v_n != ''
  vals <- sort(unique(c(v_r[keep_r], v_n[keep_n])))
  if (length(vals) == 0) {
    return(list(test = data.frame(variable = var, label = label, test = 'NA', p_value = 'NA', interpretation = 'No non-missing data.', stringsAsFactors = FALSE), levels = data.frame()))
  }
  g <- c(rep('Responder_362', sum(keep_r)), rep('NonResponder_453', sum(keep_n)))
  x <- c(v_r[keep_r], v_n[keep_n])
  tab <- table(g, x)

  test <- 'Chi-square test'; p <- NA
  if (all(dim(tab) >= c(2, 2))) {
    if (all(dim(tab) == c(2, 2))) {
      exp_vals <- tryCatch(chisq.test(tab, correct = FALSE)$expected, error = function(e) matrix(10, nrow = 2, ncol = 2))
      if (any(exp_vals < 5)) {
        test <- 'Fisher exact test'; p <- tryCatch(fisher.test(tab)$p.value, error = function(e) NA)
      } else {
        p <- tryCatch(chisq.test(tab, correct = FALSE)$p.value, error = function(e) NA)
      }
    } else {
      base_chi <- tryCatch(chisq.test(tab), error = function(e) NULL)
      if (!is.null(base_chi) && any(base_chi$expected < 5)) {
        test <- 'Chi-square test (simulated p)'
        p <- tryCatch(chisq.test(tab, simulate.p.value = TRUE, B = 20000)$p.value, error = function(e) NA)
      } else {
        p <- if (!is.null(base_chi)) base_chi$p.value else NA
      }
    }
  }

  interp <- interpret_p(p)
  r_total <- sum(keep_r); n_total <- sum(keep_n)
  lev_rows <- list()
  for (lv in vals) {
    lv_label <- lv
    if (!is.null(labels) && lv %in% names(labels)) lv_label <- labels[[lv]]
    lev_rows[[length(lev_rows) + 1]] <- data.frame(
      variable = var, label = label, level_code = lv, level_label = lv_label,
      responder = fmt_n_pct(sum(v_r[keep_r] == lv), r_total),
      nonresponder = fmt_n_pct(sum(v_n[keep_n] == lv), n_total),
      test = test, p_value = p_fmt(p), interpretation = interp,
      stringsAsFactors = FALSE
    )
  }
  list(test = data.frame(variable = var, label = label, test = test, p_value = p_fmt(p), interpretation = interp, stringsAsFactors = FALSE),
       levels = do.call(rbind, lev_rows))
}

checkbox_compare <- function(var, label) {
  r_yes <- sum(!is_missing(resp[[var]])); r_no <- nrow(resp) - r_yes
  n_yes <- sum(!is_missing(non[[var]])); n_no <- nrow(non) - n_yes
  tab <- matrix(c(r_yes, r_no, n_yes, n_no), nrow = 2, byrow = TRUE)
  exp_vals <- tryCatch(chisq.test(tab, correct = FALSE)$expected, error = function(e) matrix(10, nrow = 2, ncol = 2))
  if (any(exp_vals < 5)) {
    test <- 'Fisher exact test'; p <- tryCatch(fisher.test(tab)$p.value, error = function(e) NA)
  } else {
    test <- 'Chi-square test'; p <- tryCatch(chisq.test(tab, correct = FALSE)$p.value, error = function(e) NA)
  }
  data.frame(variable = var, label = label,
             responder_selected = fmt_n_pct(r_yes, nrow(resp)),
             nonresponder_selected = fmt_n_pct(n_yes, nrow(non)),
             test = test, p_value = p_fmt(p), interpretation = interpret_p(p), stringsAsFactors = FALSE)
}

confidence_compare <- function(var, label) {
  x_r <- to_num(resp[[var]]); x_n <- to_num(non[[var]])
  x_r <- x_r[!is.na(x_r)]; x_n <- x_n[!is.na(x_n)]
  p <- NA
  if (length(x_r) > 0 && length(x_n) > 0) p <- tryCatch(wilcox.test(x_r, x_n)$p.value, error = function(e) NA)
  direction <- NULL
  if (!is.na(p) && p < 0.05) direction <- ifelse(mean(x_r) > mean(x_n), sprintf('Responders had higher confidence for %s (p<0.05).', label), sprintf('Responders had lower confidence for %s (p<0.05).', label))
  data.frame(variable = var, label = label,
             responder_n = length(x_r), responder_mean = ifelse(length(x_r) > 0, sprintf('%.2f', mean(x_r)), 'NA'), responder_sd = ifelse(length(x_r) > 1, sprintf('%.2f', sd(x_r)), 'NA'),
             nonresponder_n = length(x_n), nonresponder_mean = ifelse(length(x_n) > 0, sprintf('%.2f', mean(x_n)), 'NA'), nonresponder_sd = ifelse(length(x_n) > 1, sprintf('%.2f', sd(x_n)), 'NA'),
             test = 'Wilcoxon rank-sum', p_value = p_fmt(p), interpretation = interpret_p(p, direction), stringsAsFactors = FALSE)
}

age_table <- numeric_compare('q0005', var_name_map[['q0005']])

core_vars <- c('q0006', 'q0008', 'q0009', 'q0011', 'q0012', 'q0007', 'q0015', 'q0016', 'q0017')
core_tests <- list(); core_levels <- list()
for (v in core_vars) {
  z <- categorical_compare(v, var_name_map[[v]], labels_map[[v]])
  core_tests[[length(core_tests) + 1]] <- z$test
  if (nrow(z$levels) > 0) core_levels[[length(core_levels) + 1]] <- z$levels
}
core_tests_df <- do.call(rbind, core_tests)
core_levels_df <- do.call(rbind, core_levels)

training_df <- do.call(rbind, lapply(names(checkbox_labels_training), function(v) checkbox_compare(v, checkbox_labels_training[[v]])))
barrier_df <- do.call(rbind, lapply(names(checkbox_labels_barriers), function(v) checkbox_compare(v, checkbox_labels_barriers[[v]])))
conf_df <- do.call(rbind, lapply(names(confidence_labels), function(v) confidence_compare(v, confidence_labels[[v]])))

conf_vars <- names(confidence_labels)
resp_conf_mean <- apply(sapply(resp[, conf_vars, drop = FALSE], to_num), 1, function(x) ifelse(all(is.na(x)), NA, mean(x, na.rm = TRUE)))
non_conf_mean <- apply(sapply(non[, conf_vars, drop = FALSE], to_num), 1, function(x) ifelse(all(is.na(x)), NA, mean(x, na.rm = TRUE)))
resp_conf_mean <- resp_conf_mean[!is.na(resp_conf_mean)]; non_conf_mean <- non_conf_mean[!is.na(non_conf_mean)]
conf_overall_p <- if (length(resp_conf_mean) > 0 && length(non_conf_mean) > 0) tryCatch(wilcox.test(resp_conf_mean, non_conf_mean)$p.value, error = function(e) NA) else NA
conf_overall <- data.frame(
  variable = 'confidence_overall_mean16', label = 'Overall confidence index (mean of 16 items)',
  responder_n = length(resp_conf_mean), responder_mean = ifelse(length(resp_conf_mean) > 0, sprintf('%.2f', mean(resp_conf_mean)), 'NA'), responder_sd = ifelse(length(resp_conf_mean) > 1, sprintf('%.2f', sd(resp_conf_mean)), 'NA'),
  nonresponder_n = length(non_conf_mean), nonresponder_mean = ifelse(length(non_conf_mean) > 0, sprintf('%.2f', mean(non_conf_mean)), 'NA'), nonresponder_sd = ifelse(length(non_conf_mean) > 1, sprintf('%.2f', sd(non_conf_mean)), 'NA'),
  test = 'Wilcoxon rank-sum', p_value = p_fmt(conf_overall_p), interpretation = interpret_p(conf_overall_p), stringsAsFactors = FALSE)

knowledge_num <- do.call(rbind, list(
  numeric_compare('q0015', var_name_map[['q0015']]),
  numeric_compare('q0016', var_name_map[['q0016']]),
  numeric_compare('q0017', var_name_map[['q0017']])
))

count_by <- function(x) {
  x <- trim_vec(x); x <- x[x != '']
  tb <- table(x)
  data.frame(state_code = names(tb), n = as.integer(tb), stringsAsFactors = FALSE)
}
state_r <- count_by(resp$q0007); state_n <- count_by(non$q0007)
state <- merge(state_r, state_n, by = 'state_code', all = TRUE, suffixes = c('_responder', '_nonresponder'))
state$n_responder[is.na(state$n_responder)] <- 0
state$n_nonresponder[is.na(state$n_nonresponder)] <- 0
state$total_n <- state$n_responder + state$n_nonresponder
state$completion_rate <- ifelse(state$total_n > 0, state$n_responder / state$total_n, NA)
state$completion_rate_pct <- sprintf('%.1f%%', 100 * state$completion_rate)
state <- state[order(-state$n_responder, -state$total_n), ]

state_top_completers <- head(state[, c('state_code', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct')], 10)
state_no_matched <- state[state$n_responder == 0, c('state_code', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct')]
state_ge10 <- state[state$total_n >= 10, ]
state_high <- state_ge10[state_ge10$completion_rate == max(state_ge10$completion_rate, na.rm = TRUE), c('state_code', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct')]
state_low <- state_ge10[state_ge10$completion_rate == min(state_ge10$completion_rate, na.rm = TRUE), c('state_code', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct')]
state_extremes <- rbind(
  cbind(metric = 'Highest completion rate (states with total_n>=10)', state_high),
  cbind(metric = 'Lowest completion rate (states with total_n>=10)', state_low)
)
state_counts_summary <- data.frame(
  metric = c('States represented in analysis set', 'States with <10 total respondents', 'States with >=10 total respondents', 'States with no matched responder cases'),
  value = c(nrow(state), sum(state$total_n < 10), sum(state$total_n >= 10), nrow(state_no_matched)),
  stringsAsFactors = FALSE
)

# outputs
write.csv(age_table, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_age_numeric_test.csv'), row.names = FALSE)
write.csv(core_tests_df, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_categorical_tests.csv'), row.names = FALSE)
write.csv(core_levels_df, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_categorical_levels.csv'), row.names = FALSE)
write.csv(training_df, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_training_checkbox_tests.csv'), row.names = FALSE)
write.csv(barrier_df, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_barrier_checkbox_tests.csv'), row.names = FALSE)
write.csv(conf_df, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_confidence_item_tests.csv'), row.names = FALSE)
write.csv(conf_overall, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_confidence_overall_test.csv'), row.names = FALSE)
write.csv(knowledge_num, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_knowledge_numeric_tests.csv'), row.names = FALSE)
write.csv(state, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_state_completion_table.csv'), row.names = FALSE)
write.csv(state_top_completers, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_state_top_completers.csv'), row.names = FALSE)
write.csv(state_no_matched, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_state_no_matched_cases.csv'), row.names = FALSE)
write.csv(state_extremes, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_state_rate_extremes_n_ge_10.csv'), row.names = FALSE)
write.csv(state_counts_summary, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_state_counts_summary.csv'), row.names = FALSE)

sig <- core_tests_df[core_tests_df$p_value != 'NA' & as.numeric(gsub('<','',core_tests_df$p_value)) < 0.05, c('label','test','p_value')]
summary_lines <- c(
  sprintf('Responders (colleague matched): %d', nrow(resp)),
  sprintf('Non-responders (old logic, excludes all-3-contact-missing): %d', nrow(non)),
  'Statistical framework: Age via Welch t-test; categorical via Chi-square/Fisher exact; confidence via Wilcoxon rank-sum.'
)
if (nrow(sig) > 0) {
  summary_lines <- c(summary_lines, 'Variables with p<0.05:')
  for (i in seq_len(nrow(sig))) summary_lines <- c(summary_lines, sprintf('- %s (%s, p=%s)', sig$label[i], sig$test[i], sig$p_value[i]))
} else {
  summary_lines <- c(summary_lines, 'No categorical core variable crossed p<0.05.')
}
writeLines(summary_lines, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_summary.txt'))

html <- paste0(
  '<html><body style="font-family: Helvetica, Arial, sans-serif;">',
  '<h1>Analysis 2 (Old Logic): Responder 362 vs Non-Responder 453</h1>',
  '<p>Date: ', Sys.Date(), '</p>',
  '<p>Non-responder set rule: all non-responders excluding rows where ID, name, and email are all missing.</p>',
  '<p>Sample sizes: responders n=362; non-responders n=453.</p>',
  '<h2>Age</h2>', df_to_html(age_table, 'Age Comparison (Welch t-test)'),
  '<h2>Core Demographic/Knowledge Variables</h2>', df_to_html(core_tests_df, 'Variable-Level Statistical Tests'), df_to_html(core_levels_df, 'Category Proportions by Group'),
  '<h2>Formal Training in Handling GBV (Q0010)</h2>', df_to_html(training_df, 'Checkbox Item Comparisons'),
  '<h2>Barriers (Q0013)</h2>', df_to_html(barrier_df, 'Checkbox Item Comparisons'),
  '<h2>Confidence (Q0014)</h2>', df_to_html(conf_df, 'Item-Level Confidence Comparisons'), df_to_html(conf_overall, 'Overall Confidence Index'),
  '<h2>Knowledge Levels (Q0015-Q0017): Numeric View</h2>', df_to_html(knowledge_num, 'Numeric Score Comparisons'),
  '<h2>Geographic Patterns (State)</h2>',
  df_to_html(state_top_completers, 'States with Largest Absolute Number of Completers'),
  df_to_html(state_no_matched, 'States with No Matched Cases'),
  df_to_html(state_extremes, 'Highest/Lowest Completion Rates (States with total_n>=10)'),
  df_to_html(state_counts_summary, 'Counts of States by Size / Matched Cases'),
  '<h2>Interpretation</h2><ul>', paste0('<li>', escape_html(summary_lines), '</li>', collapse=''), '</ul>',
  '</body></html>'
)
writeLines(html, file.path(out_dir, 'rerun2026_analysis2_oldlogic453_report.html'))

cat('Done\n')
