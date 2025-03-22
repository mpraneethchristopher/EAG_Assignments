// Initialize extension
chrome.runtime.onInstalled.addListener(async () => {
  // Create context menu
  chrome.contextMenus.create({
    id: 'translateToGerman',
    title: 'Translate to German',
    contexts: ['selection']
  });

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

const GEMINI_API_KEY = 'AIzaSyA01RkTCmXN00eLWt1fEsPCmqR5Jg_bkMM';

// Handle tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url && (tab.url.startsWith('http://') || tab.url.startsWith('https://'))) {
    chrome.scripting.executeScript({
      target: { tabId: tabId },
      files: ['content.js']
    }).catch(err => console.error('Failed to inject content script:', err));
  }
});

// Function to translate text
async function translateText(text, tabId) {
  if (!text) {
    console.log('No text to translate');
    return;
  }

  console.log('Translating text:', text);
  
  try {
    const response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' + GEMINI_API_KEY, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        contents: [{
          parts: [{
            text: `You are a translator. Translate this English text to German: "${text}". Only respond with the German translation, nothing else.`
          }]
        }],
        safetySettings: [{
          category: "HARM_CATEGORY_DANGEROUS_CONTENT",
          threshold: "BLOCK_NONE"
        }]
      })
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('API Error:', errorData);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('API Response:', data);

    if (data.candidates && data.candidates[0] && data.candidates[0].content && data.candidates[0].content.parts && data.candidates[0].content.parts[0].text) {
      const translation = data.candidates[0].content.parts[0].text.trim();
      console.log('Translation:', translation);
      
      // Send translation to content script
      chrome.tabs.sendMessage(tabId, {
        action: 'showTranslation',
        translation: translation
      }).catch(error => {
        // If message fails, try re-injecting content script and sending again
        chrome.scripting.executeScript({
          target: { tabId: tabId },
          files: ['content.js']
        }).then(() => {
          chrome.tabs.sendMessage(tabId, {
            action: 'showTranslation',
            translation: translation
          });
        }).catch(err => console.error('Failed to inject content script:', err));
      });
    } else {
      throw new Error('Invalid API response format');
    }
  } catch (error) {
    console.error('Translation error:', error);
    // Send error to content script
    chrome.tabs.sendMessage(tabId, {
      action: 'showTranslation',
      translation: 'Translation error: ' + error.message
    }).catch(err => {
      // If message fails, try re-injecting content script and sending again
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