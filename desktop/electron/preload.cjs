'use strict';

const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('riskflowDesktop', {
  platform: process.platform,
  arch: process.arch,
});
