// Create context menu item
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'translateToGerman',
    title: 'Translate to German',
    contexts: ['selection']
  });
});

const GEMINI_API_KEY = 'AIzaSyA01RkTCmXN00eLWt1fEsPCmqR5Jg_bkMM';

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
        console.error('Error sending translation to content script:', error);
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
      console.error('Error sending error message to content script:', err);
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