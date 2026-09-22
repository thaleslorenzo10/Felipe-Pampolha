// Vibe Coding Toolkit: cópias originais em eslint-rules; nenhum código de negócio alterado.
import js from '@eslint/js';
import html from 'eslint-plugin-html';
import globals from 'globals';
import quality from './eslint-rules/index.cjs';
export default [
  { ignores: ['eslint-rules/verify.mjs', 'node_modules/**', '.claude/**', '.codex/**', 'graphify-out/**', '.venv/**', 'venv/**', 'dist/**', 'output/**'] },
  {
    files: ['**/*.{js,mjs,cjs,html}'],
    plugins: { quality },
    languageOptions: { ecmaVersion: 'latest', globals: { ...globals.browser, ...globals.node } },
    rules: {
      ...js.configs.recommended.rules,
      'no-unused-vars': 'warn', // baseline 8 ocorrências
      'no-useless-escape': 'warn', // baseline 50 ocorrências
      // Baseline de quality: max-lines 1; console 5.
      'quality/max-lines': ['warn', { max: 350, includeTests: true }],
      'quality/no-direct-console': 'warn',
    },
  },
  {
    files: ['**/*.html'],
    plugins: { html },
    languageOptions: { sourceType: 'script', globals: { Chart: 'readonly', fbq: 'readonly' } },
    // O gate original isenta index.*; max-lines complementa o orçamento de JS inline.
    rules: { 'max-lines': ['warn', { max: 350 }] },
    // HTML/CSS não recebe lint semântico.
  },
  { files: ['**/*.cjs'], languageOptions: { sourceType: 'commonjs' } },
];
