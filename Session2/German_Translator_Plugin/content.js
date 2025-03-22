// Create and inject CSS for the translation popup
const style = document.createElement('style');
style.textContent = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

  .translation-popup {
    position: fixed;
    border: none;
    border-radius: 12px;
    padding: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    z-index: 10000;
    max-width: 320px;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 15px;
    line-height: 1.5;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
    background: linear-gradient(145deg, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.85));
    color: #2c3e50;
    border: 1px solid rgba(255, 255, 255, 0.3);
    opacity: 0;
    transform: translateY(10px);
    animation: popupFadeIn 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards;
  }

  @keyframes popupFadeIn {
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .translation-popup.dark-theme {
    background: linear-gradient(145deg, rgba(33, 33, 33, 0.95), rgba(33, 33, 33, 0.85));
    color: #e0e0e0;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .translation-popup .close-btn {
    position: absolute;
    right: 12px;
    top: 12px;
    cursor: pointer;
    font-size: 20px;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: transparent;
    color: #666;
    opacity: 0.7;
    transition: all 0.2s ease;
  }

  .translation-popup .close-btn:hover {
    opacity: 1;
    background: rgba(0, 0, 0, 0.05);
  }

  .dark-theme .close-btn {
    color: #e0e0e0;
  }

  .dark-theme .close-btn:hover {
    background: rgba(255, 255, 255, 0.1);
  }

  .translation-popup p {
    margin: 0;
    padding-right: 24px;
    font-weight: 400;
  }

  .translation-popup.error {
    background: linear-gradient(145deg, rgba(253, 236, 234, 0.95), rgba(253, 236, 234, 0.85));
    color: #d32f2f;
    border: 1px solid rgba(211, 47, 47, 0.1);
  }

  .translation-popup::before {
    content: '';
    position: absolute;
    top: -6px;
    left: 20px;
    width: 12px;
    height: 12px;
    background: inherit;
    border-top: 1px solid rgba(255, 255, 255, 0.3);
    border-left: 1px solid rgba(255, 255, 255, 0.3);
    transform: rotate(45deg);
    pointer-events: none;
  }
`;
document.head.appendChild(style);

let lastSelectedText = '';
let currentPopup = null;

// Function to detect if the webpage is using a dark theme
function isDarkTheme() {
  const backgroundColor = window.getComputedStyle(document.body).backgroundColor;
  const rgb = backgroundColor.match(/\d+/g);
  if (!rgb) return false;
  
  // Calculate relative luminance
  const luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
  return luminance < 0.5;
}

// Function to get computed styles
function getComputedStylesForElement(element) {
  const computedStyle = window.getComputedStyle(element);
  return {
    backgroundColor: computedStyle.backgroundColor,
    color: computedStyle.color,
    fontFamily: computedStyle.fontFamily
  };
}

// Function to get the most contrasting color
function getContrastColor(bgColor) {
  let rgb = bgColor.match(/\d+/g);
  if (!rgb) return '#000000';

  const luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
  return luminance > 0.5 ? '#2c3e50' : '#e0e0e0';
}

// Add debounce function to avoid too many API calls
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Function to remove existing popup
function removeExistingPopup() {
  if (currentPopup) {
    currentPopup.style.opacity = '0';
    currentPopup.style.transform = 'translateY(10px)';
    setTimeout(() => {
      if (currentPopup) {
        currentPopup.remove();
        currentPopup = null;
      }
    }, 300);
  }
}

// Function to create and show popup
function showPopup(text, isError = false) {
  removeExistingPopup();

  const popup = document.createElement('div');
  popup.className = 'translation-popup' + (isError ? ' error' : '') + (isDarkTheme() ? ' dark-theme' : '');
  
  const closeBtn = document.createElement('span');
  closeBtn.className = 'close-btn';
  closeBtn.textContent = '×';
  closeBtn.onclick = removeExistingPopup;
  
  const content = document.createElement('p');
  content.textContent = text;
  
  popup.appendChild(closeBtn);
  popup.appendChild(content);
  
  // Position popup near selected text
  const selection = window.getSelection();
  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    // Calculate position to keep popup in viewport
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    popup.style.visibility = 'hidden';
    document.body.appendChild(popup);
    
    const popupRect = popup.getBoundingClientRect();
    let left = rect.left + window.scrollX;
    let top = rect.bottom + window.scrollY + 5;
    
    // Adjust horizontal position if popup would overflow viewport
    if (left + popupRect.width > viewportWidth) {
      left = viewportWidth - popupRect.width - 10;
    }
    
    // Adjust vertical position if popup would overflow viewport
    if (top + popupRect.height > window.scrollY + viewportHeight) {
      top = rect.top + window.scrollY - popupRect.height - 5;
      popup.style.setProperty('--arrow-top', 'auto');
      popup.style.setProperty('--arrow-bottom', '-6px');
    }
    
    popup.style.left = `${Math.max(10, left)}px`;
    popup.style.top = `${Math.max(10, top)}px`;
    popup.style.visibility = 'visible';
  }
  
  currentPopup = popup;
  
  // Close popup when clicking outside
  document.addEventListener('click', function closePopup(e) {
    if (currentPopup && !currentPopup.contains(e.target)) {
      removeExistingPopup();
      document.removeEventListener('click', closePopup);
    }
  });
}

// Handle text selection
document.addEventListener('selectionchange', debounce(() => {
  const selection = window.getSelection();
  const selectedText = selection.toString().trim();
  
  if (selectedText.length > 0 && selectedText !== lastSelectedText) {
    lastSelectedText = selectedText;
    chrome.runtime.sendMessage({
      action: 'translateText',
      text: selectedText
    });
  } else if (selectedText.length === 0) {
    removeExistingPopup();
  }
}, 700));

// Listen for translation results
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showTranslation') {
    const isError = request.translation.startsWith('Translation error:');
    showPopup(request.translation, isError);
  }
}); 