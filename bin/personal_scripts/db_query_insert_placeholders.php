<?php

$query = $argv[1];
$subs = $argv[2];

$pairs = explode('||', $subs);
foreach ($pairs as $pair) {
  list($key, $value) = explode('==', $pair);
  $placeholders[$key] = "'" . $value . "'";
}

$query_with_values = str_replace(
  array_keys($placeholders),
  array_values($placeholders),
  $query
);
print $query_with_values . PHP_EOL;