<?php

// Get the current styles.
$cell_styles = sandcastle_get_setting('bcp-cell-styles');
// Create an array defining all of the new styles.
$new_styles = _sandcastle_style_catalog_styles();

// Add new cell styles to existing ones.
foreach($cell_styles as $type => &$styles) {
  if (!empty($new_styles[$type])) {
    $styles = array_merge($styles, $new_styles[$type]);
  }
}

// Update the setting.
sandcastle_set_setting('bcp-cell-styles', $cell_styles);
drupal_set_message(t('Cell styles have been updated with the new style catalog.'));
