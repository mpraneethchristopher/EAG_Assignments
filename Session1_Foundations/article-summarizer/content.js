// Function to extract article content from the page
function extractArticleContent() {
  // Try to get content from article or main content area
  let content = '';
  
  // For Wikipedia pages
  if (window.location.hostname.includes('wikipedia.org')) {
    const contentElement = document.getElementById('mw-content-text');
    if (contentElement) {
      // Get all paragraphs but exclude references and navigation boxes
      const paragraphs = Array.from(contentElement.getElementsByTagName('p'))
        .filter(p => !p.closest('.reference') && !p.closest('.navbox'));
      content = paragraphs.map(p => p.textContent).join('\n');
    }
  } else {
    // For general articles
    // Try to find the main article content using common selectors
    const selectors = [
      'article',
      '[role="main"]',
      '.post-content',
      '.article-content',
      '.entry-content',
      'main'
    ];

    let mainContent = null;
    for (const selector of selectors) {
      mainContent = document.querySelector(selector);
      if (mainContent) break;
    }

    if (mainContent) {
      const paragraphs = mainContent.getElementsByTagName('p');
      content = Array.from(paragraphs).map(p => p.textContent).join('\n');
    }

    // If no content found with selectors, get all paragraphs from body
    if (!content) {
      const bodyParagraphs = document.getElementsByTagName('p');
      content = Array.from(bodyParagraphs).map(p => p.textContent).join('\n');
    }
  }

  return content.trim();
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getArticleContent') {
    const content = extractArticleContent();
    sendResponse({ content });
  }
  return true;
}); 