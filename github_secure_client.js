// Secure GitHub client for safe file operations
// Uses JSON communication to prevent code injection

const { getUncachableGitHubClient } = require('./github_client.js');
const fs = require('fs');
const path = require('path');

async function uploadFileSecure(config) {
  try {
    // Validate input parameters
    if (!config.owner || !config.repo || !config.path) {
      throw new Error('Missing required parameters: owner, repo, path');
    }

    // Sanitize inputs
    const sanitizedConfig = {
      owner: String(config.owner).trim(),
      repo: String(config.repo).trim(),
      path: String(config.path).trim(),
      message: String(config.message || 'Update file').trim(),
      content: config.content || '',
      branch: String(config.branch || 'main').trim()
    };

    // Validate path doesn't contain dangerous characters
    if (sanitizedConfig.path.includes('..') || sanitizedConfig.path.startsWith('/')) {
      throw new Error('Invalid file path');
    }

    const octokit = await getUncachableGitHubClient();
    
    // Check if file exists to get SHA for updates
    let sha = null;
    try {
      const { data } = await octokit.rest.repos.getContent({
        owner: sanitizedConfig.owner,
        repo: sanitizedConfig.repo,
        path: sanitizedConfig.path
      });
      sha = data.sha;
    } catch (err) {
      // File doesn't exist, will create new
    }
    
    // Convert content to base64
    const content = Buffer.from(sanitizedConfig.content, 'utf8').toString('base64');
    
    const result = await octokit.rest.repos.createOrUpdateFileContents({
      owner: sanitizedConfig.owner,
      repo: sanitizedConfig.repo,
      path: sanitizedConfig.path,
      message: sanitizedConfig.message,
      content: content,
      branch: sanitizedConfig.branch,
      ...(sha && { sha })
    });
    
    console.log(JSON.stringify({
      status: "success",
      path: sanitizedConfig.path,
      sha: result.data.content.sha,
      html_url: result.data.content.html_url
    }));
    
  } catch (error) {
    console.log(JSON.stringify({
      status: "error",
      error: error.message,
      stack: error.stack
    }));
    process.exit(1);
  }
}

// Read config from file and execute
const configPath = process.argv[2];
if (!configPath) {
  console.log(JSON.stringify({
    status: "error",
    error: "Config file path required"
  }));
  process.exit(1);
}

try {
  const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  uploadFileSecure(config);
} catch (error) {
  console.log(JSON.stringify({
    status: "error",
    error: error.message
  }));
  process.exit(1);
}