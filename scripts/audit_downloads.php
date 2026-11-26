<?php
/** Read-only WooCommerce download metadata audit, executed via WP-CLI. */
if (!defined('WP_CLI') || !WP_CLI) { exit("Run with WP-CLI.\n"); }
global $wpdb;
$rows = $wpdb->get_results("SELECT meta_value FROM {$wpdb->postmeta} WHERE meta_key='_downloadable_files'");
if ($wpdb->last_error) { WP_CLI::error('Cannot query download metadata'); }
$home_host = preg_replace('/^www\./', '', wp_parse_url(home_url(), PHP_URL_HOST));
$roots = [realpath(ABSPATH)];
$private = getenv('PRIVATE_DOWNLOAD_ROOT');
if ($private && realpath($private)) { $roots[] = realpath($private); }
$counts = ['entries' => 0, 'readable' => 0, 'missing' => 0, 'external' => 0, 'invalid' => 0];
foreach ($rows as $row) {
    $files = maybe_unserialize($row->meta_value);
    if (empty($files)) { continue; }
    if (!is_array($files)) { $counts['invalid']++; continue; }
    foreach ($files as $entry) {
        $counts['entries']++;
        if (!is_array($entry) || empty($entry['file']) || !is_string($entry['file'])) {
            $counts['invalid']++; continue;
        }
        $path = $entry['file'];
        if (str_starts_with($path, 'file://')) { $path = substr($path, 7); }
        if (preg_match('#^https?://#i', $path)) {
            $url = wp_parse_url($path);
            if (preg_replace('/^www\./', '', $url['host'] ?? '') !== $home_host) {
                $counts['external']++; continue;
            }
            $path = ABSPATH . ltrim(rawurldecode($url['path'] ?? ''), '/');
        }
        if (!str_starts_with($path, '/')) { $counts['invalid']++; continue; }
        $real = realpath($path);
        if (!$real || !is_file($real) || !is_readable($real)) { $counts['missing']++; continue; }
        $allowed = false;
        foreach ($roots as $root) {
            if ($root && str_starts_with($real, rtrim($root, '/') . '/')) { $allowed = true; break; }
        }
        if (!$allowed) { $counts['invalid']++; continue; }
        $counts['readable']++;
    }
}
WP_CLI::log(wp_json_encode($counts));
if (!$counts['entries'] || $counts['missing'] || $counts['external'] || $counts['invalid']) {
    WP_CLI::error('Download metadata requires private review; no records were changed');
}
WP_CLI::success('All audited download entries resolve to readable allowed local files');
