let proxyConfig = { username: '', password: '' };

async function loadProxyConfig() {
  try {
    const url = chrome.runtime.getURL('proxy_config.json');
    const response = await fetch(url);
    proxyConfig = await response.json();
    console.log('Proxy config loaded:', proxyConfig);
  } catch (err) {
    console.error('Failed to load proxy config:', err);
  }
}

loadProxyConfig();

chrome.webRequest.onAuthRequired.addListener(
  (details, callbackFn) => {
    console.log('Auth required for:', details.url);
    if (proxyConfig.username && proxyConfig.password) {
      console.log('Providing auth credentials');
      callbackFn({
        authCredentials: {
          username: proxyConfig.username,
          password: proxyConfig.password
        }
      });
    } else {
      console.log('No proxy credentials configured');
      callbackFn({});
    }
  },
  { urls: ['<all_urls>'] },
  ['asyncBlocking']
);
