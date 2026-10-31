'use strict';
// Disposable qualification data only. Never point this script at a business DB.
const fs = require('node:fs');
const { randomUUID } = require('node:crypto');
const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const { createModels, runAsSystem } = require('@librechat/data-schemas');
const { applyQualificationRoles } = require('./scout-qualification-policy.cjs');

(async () => {
  if (process.env.MONGO_URI !== 'mongodb://mongo:27017/ScoutQualification') {
    throw new Error('Refusing unexpected database');
  }
  if (!process.env.QA_USER_PASSWORD) throw new Error('Disposable password missing');
  const manifestPath = '/app/data/qualification-fixtures.json';
  if (fs.existsSync(manifestPath)) throw new Error('Fixtures already exist; do not reseed');
  let ready = false;
  for (let attempt = 0; attempt < 40; attempt++) {
    try {
      const response = await fetch('http://127.0.0.1:3080/api/convos', { signal: AbortSignal.timeout(1500) });
      if (response.status === 401) { ready = true; break; }
    } catch { /* Wait until startup has initialized the platform policy. */ }
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  if (!ready) throw new Error('Disposable server did not become ready');
  const models = createModels(mongoose);
  await mongoose.connect(process.env.MONGO_URI);
  await Promise.all(Object.values(models).filter((model) => typeof model.init === 'function').map((model) => model.init()));
  await applyQualificationRoles(models);
  const fixtures = [];
  const password = await bcrypt.hash(process.env.QA_USER_PASSWORD, 10);
  await runAsSystem(async () => {
    for (const [name, tenantId, email] of [
      ['staff-one', 'staff', 'staff-one@qualification.invalid'],
      ['staff-two', 'staff', 'staff-two@qualification.invalid'],
      ['customer-a', 'customer-a', 'customer@qualification.invalid'],
      ['customer-b', 'customer-b', 'customer@qualification.invalid'],
    ]) {
      const user = await models.User.create({ name, username: name, email, password,
        tenantId, emailVerified: true, provider: 'local', role: 'USER' });
      const conversationId = randomUUID();
      const messageId = randomUUID();
      const fileId = randomUUID();
      const marker = `SCOUT_PRIVATE_${name.toUpperCase().replaceAll('-', '_')}`;
      const message = await models.Message.create({ messageId, conversationId,
        user: user.id, tenantId, sender: 'User', text: marker, isCreatedByUser: true });
      await models.Conversation.create({ conversationId, title: marker,
        user: user.id, tenantId, messages: [message._id], endpoint: 'openAI' });
      await models.File.create({ user: user._id, tenantId, file_id: fileId,
        bytes: Buffer.byteLength(marker), filename: `${name}-private.txt`,
        filepath: `/qualification/${fileId}`, type: 'text/plain', source: 'text',
        text: marker, conversationId, messageId });
      fixtures.push({ name, tenantId, email, userId: user.id,
        conversationId, messageId, fileId, marker });
    }
  });
  fs.writeFileSync(manifestPath, JSON.stringify(fixtures, null, 2), { mode: 0o600 });
  await mongoose.disconnect();
  console.log(JSON.stringify({ seeded: fixtures.length, tenants: 3,
    conversations: 4, messages: 4, textFiles: 4, providerCalls: 0 }));
})().catch(async (error) => {
  console.error(error.name + ': ' + error.message);
  await mongoose.disconnect(); process.exitCode = 1;
});
