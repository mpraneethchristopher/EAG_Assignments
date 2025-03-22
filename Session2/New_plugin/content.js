// Create and inject CSS for the translation popup
const style = document.createElement('style');
style.textContent = `
  .translation-popup {
    position: fixed;
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    padding: 15px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    z-index: 10000;
    max-width: 300px;
    font-family: inherit;
    font-size: 14px;
    line-height: 1.4;
    transition: all 0.2s ease;
    backdrop-filter: blur(10px);
  }
  .translation-popup .close-btn {
    position: absolute;
    right: 8px;
    top: 8px;
    cursor: pointer;
    font-size: 18px;
    padding: 4px;
    opacity: 0.7;
    transition: opacity 0.2s ease;
  }
  .translation-popup .close-btn:hover {
    opacity: 1;
  }
  .translation-popup p {
    margin: 0;
    padding-right: 20px;
  }
  .translation-popup.error {
    background: rgba(255, 0, 0, 0.1) !important;
    color: #d32f2f !important;
  }
`;
document.head.appendChild(style);

let lastSelectedText = '';
let currentPopup = null;

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
  // Convert background color to RGB if it's in rgba format
  let rgb = bgColor.match(/\d+/g);
  if (!rgb) return '#000000';

  // Calculate relative luminance
  const luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255;
  return luminance > 0.5 ? '#000000' : '#ffffff';
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
    currentPopup.remove();
    currentPopup = null;
  }
}

// Function to create and show popup
function showPopup(text, isError = false) {
  removeExistingPopup();

  const popup = document.createElement('div');
  popup.className = 'translation-popup' + (isError ? ' error' : '');
  
  const closeBtn = document.createElement('span');
  closeBtn.className = 'close-btn';
  closeBtn.textContent = '×';
  closeBtn.onclick = removeExistingPopup;
  
  const content = document.createElement('p');
  content.textContent = text;
  
  popup.appendChild(closeBtn);
  popup.appendChild(content);
  
  // Position popup near selected text and apply styles
  const selection = window.getSelection();
  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    // Get the selected element's styles
    const selectedElement = selection.anchorNode.parentElement;
    const styles = getComputedStylesForElement(selectedElement);
    
    // Apply the webpage's styles to the popup
    popup.style.backgroundColor = styles.backgroundColor;
    popup.style.color = styles.color;
    popup.style.fontFamily = styles.fontFamily;
    
    // Ensure text is readable by adjusting colors if needed
    if (styles.backgroundColor === 'rgba(0, 0, 0, 0)' || styles.backgroundColor === 'transparent') {
      popup.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
    }
    
    // Add slight transparency to background
    const bgColor = window.getComputedStyle(popup).backgroundColor;
    if (bgColor.startsWith('rgb')) {
      popup.style.backgroundColor = bgColor.replace('rgb', 'rgba').replace(')', ', 0.95)');
    }
    
    // Adjust close button color for contrast
    closeBtn.style.color = getContrastColor(popup.style.backgroundColor);
    
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
}, 700)); // Increased delay to 700ms for better user experience

// Listen for translation results
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'showTranslation') {
    const isError = request.translation.startsWith('Translation error:');
    showPopup(request.translation, isError);
  }
}); 