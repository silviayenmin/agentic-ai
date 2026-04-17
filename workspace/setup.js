// setup.js
const { exec } = require('child_process');

exec('npm install --save-dev eslint prettier', (error, stdout, stderr) => {
  if (error) {
    console.error(`Error: ${error}`);
  }
});

exec('npx eslint --init', (error, stdout, stderr) => {
  if (error) {
    console.error(`Error: ${error}`);
  }
});