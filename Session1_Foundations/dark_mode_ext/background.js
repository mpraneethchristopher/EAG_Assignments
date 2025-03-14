// Listen for extension icon clicks
chrome.action.onClicked.addListener((tab) => {
  // Inject the content script when the extension icon is clicked
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    files: ['darkmode.js']
  });
}); 