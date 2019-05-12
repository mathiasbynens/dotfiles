module.exports = {

  "extends": [
    "eslint:recommended",
    "plugin:import/errors",
    "plugin:import/warnings",
    "kentcdodds/possible-errors",
    "kentcdodds/best-practices",
    "kentcdodds/es6/possible-errors",
    "kentcdodds/import",
    "plugin:promise/recommended",
    "xo/esnext",
    "plugin:unicorn/recommended",
    "google"
  ],
  "plugins": [
    "unicorn",
    "import",
    "json",
    "eslint-comments",
    "optimize-regex",
    "promise"
  ],

  "env": {
    "browser": true,
    "es6": true,
    "node": true
  },

  "rules": {
    "no-console": "off",
    "indent": ["error", 2, {
      "SwitchCase": 1,
      "VariableDeclarator": 2
    }],
    "max-len": ["error", 120, {
      "ignoreComments": true,
      "ignoreUrls": true,
      "tabWidth": 2
    }],
    "no-unused-vars": ["error", {
      "vars": "all",
      "args": "after-used",
      "argsIgnorePattern": "(^reject$|^_$)",
      "varsIgnorePattern": "(^_$)"
    }],

    "eslint-comments/disable-enable-pair": "error",
    "eslint-comments/no-duplicate-disable": "error",
    "eslint-comments/no-unlimited-disable": "error",
    "eslint-comments/no-unused-disable": "error",
    "eslint-comments/no-unused-enable": "error",

    "optimize-regex/optimize-regex": "warn",

    "valid-jsdoc": "off", // it's wrong pretty often
    "comma-dangle": "off",
    "strict": "off",
    "curly": "off",
    "arrow-parens": ["error", "as-needed"],
    "no-return-assign": "off",
    "unicorn/prefer-type-error": "off",
    "require-jsdoc": "off",
    "no-implicit-coercion": "off",
    "capitalized-comments": "warn"

    }
};
