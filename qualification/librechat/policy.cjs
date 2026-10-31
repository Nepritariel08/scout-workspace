'use strict';
// Explicit provisioning for these synthetic tenants, not a production role editor.
const mongoose = require('mongoose');
const { createModels, runAsSystem } = require('@librechat/data-schemas');
async function applyQualificationRoles(models) {
  if (process.env.MONGO_URI !== 'mongodb://mongo:27017/ScoutQualification') {
    throw new Error('Refusing unexpected database');
  }
  await runAsSystem(async () => {
    const platform = await models.Role.findOne({ name: 'USER', tenantId: { $exists: false } }).lean();
    if (!platform) throw new Error('Platform policy has not been initialized');
    for (const name of ['MCP_SERVERS', 'AGENTS', 'PROMPTS', 'RUN_CODE', 'WEB_SEARCH']) {
      if (platform.permissions[name]?.USE !== false) throw new Error(`Required platform deny absent: ${name}`);
    }
    for (const tenantId of ['staff', 'customer-a', 'customer-b']) {
      await models.Role.updateOne({ name: 'USER', tenantId }, { $set: {
        permissions: platform.permissions, description: 'Synthetic qualification deny policy',
      } }, { upsert: true });
    }
  });
}
module.exports = { applyQualificationRoles };
if (require.main === module) {
  (async () => {
    const models = createModels(mongoose);
    await mongoose.connect(process.env.MONGO_URI);
    await Promise.all(Object.values(models).filter((model) => typeof model.init === 'function').map((model) => model.init()));
    await applyQualificationRoles(models);
    await mongoose.disconnect();
    console.log(JSON.stringify({ provisionedTenantPolicies: 3, role: 'USER',
      note: 'Restart the disposable app to evict previously cached default roles' }));
  })().catch(async (error) => {
    console.error(error.name + ': ' + error.message);
    await mongoose.disconnect(); process.exitCode = 1;
  });
}
