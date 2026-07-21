// Metro config — monorepo. https://docs.expo.dev/guides/monorepos/
const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);

// 1. Monorepo kökündeki tüm dosyaları izle (packages/shared dahil).
config.watchFolders = [monorepoRoot];

// 2. Paketleri önce app'in, sonra kökün node_modules'ünden çöz (hoisting).
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(monorepoRoot, 'node_modules'),
];

module.exports = config;
