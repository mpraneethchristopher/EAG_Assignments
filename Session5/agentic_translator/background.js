// Initialize extension
chrome.runtime.onInstalled.addListener(async () => {
  // Create context menu
  chrome.contextMenus.create({
    id: 'translateToGerman',
    title: 'Translate to German',
    contexts: ['selection']
  });

  // Clear previous logs
  chrome.storage.local.set({ 'translationLogs': [] });

  // Inject content script into all existing tabs
  const tabs = await chrome.tabs.query({ url: ['http://*/*', 'https://*/*'] });
  for (const tab of tabs) {
    try {
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ['content.js']
      });
    } catch (e) {
      console.error(`Failed to inject content script into tab ${tab.id}:`, e);
    }
  }
});

// Handle tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && (tab.url.startsWith('http://') || tab.url.startsWith('https://'))) {
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js']
    }).catch(err => console.error('Failed to inject content script:', err));
  }
});

// URL of our Python backend API
const API_URL = 'http://localhost:5000';

// Main translation function that calls the Python API
async function translateText(text, tabId) {
  if (!text) {
    console.log('No text to translate');
    return;
  }

  try {
    console.log('Translating text:', text);
    
    // Try the direct translation endpoint first (more reliable)
    let response = await fetch(`${API_URL}/api/direct-translate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ text })
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Direct translation API error:', errorData);
      
      // Fall back to the agentic translate endpoint
      console.log('Falling back to agentic translation endpoint...');
      response = await fetch(`${API_URL}/api/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
      });
      
      if (!response.ok) {
        const agenticErrorData = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${agenticErrorData}`);
      }
    }

    const data = await response.json();
    console.log('Translation API Response:', data);
    
    // Store the logs in Chrome storage for displaying in the popup
    if (data.logs) {
      chrome.storage.local.set({ 'translationLogs': data.logs });
    } else {
      // For direct translation without logs, create a simple log
      // This should no longer happen as we now include logs in direct-translate response
      chrome.storage.local.set({ 
        'translationLogs': [
          {
            type: 'function_call',
            function: 'directTranslate',
            params: text,
            result: data.translation,
            timestamp: Date.now()
          },
          {
            type: 'final_answer',
            translation: data.translation,
            timestamp: Date.now()
          }
        ] 
      });
    }
    
    // Send translation to content script
    chrome.tabs.sendMessage(tabId, {
      action: 'showTranslation',
      translation: data.translation,
      detectedLanguage: data.detected_language
    }).catch(error => {
      // If message fails, try re-injecting content script and sending again
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        files: ['content.js']
      }).then(() => {
        chrome.tabs.sendMessage(tabId, {
          action: 'showTranslation',
          translation: data.translation,
          detectedLanguage: data.detected_language
        });
      }).catch(err => console.error('Failed to inject content script:', err));
    });
  } catch (error) {
    console.error('Translation error:', error);
    
    // Store error log
    chrome.storage.local.get(['translationLogs'], (result) => {
      const logs = result.translationLogs || [];
      logs.push({
        type: 'error',
        message: error.message,
        timestamp: Date.now()
      });
      chrome.storage.local.set({ 'translationLogs': logs });
    });
    
    // Send error to content script
    chrome.tabs.sendMessage(tabId, {
      action: 'showTranslation',
      translation: 'Translation error: ' + error.message
    }).catch(err => {
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        files: ['content.js']
      }).then(() => {
        chrome.tabs.sendMessage(tabId, {
          action: 'showTranslation',
          translation: 'Translation error: ' + error.message
        });
      }).catch(err => console.error('Failed to inject content script:', err));
    });
  }
}

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'translateText') {
    translateText(request.text, sender.tab.id);
  } else if (request.action === 'openPopup') {
    chrome.action.openPopup();
  }
  // Must return true if response is sent asynchronously
  return true;
});

// Handle context menu click
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'translateToGerman') {
    const selectedText = info.selectionText;
    if (selectedText) {
      translateText(selectedText, tab.id);
    }
  }
}); 