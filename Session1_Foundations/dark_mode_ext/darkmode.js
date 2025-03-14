(() => {
  // Check if dark mode is already applied
  const isDarkMode = document.body.classList.contains('dark-mode-extension');

  if (!isDarkMode) {
    // Apply dark mode
    const style = document.createElement('style');
    style.textContent = `
      .dark-mode-extension,
      .dark-mode-extension * {
        background-color: #1a1a1a !important;
        color: #e6e6e6 !important;
        border-color: #333 !important;
      }
      
      .dark-mode-extension img,
      .dark-mode-extension video,
      .dark-mode-extension iframe {
        filter: brightness(0.8) !important;
      }
      
      .dark-mode-extension a {
        color: #6ea8fe !important;
      }
      
      .dark-mode-extension input,
      .dark-mode-extension textarea,
      .dark-mode-extension select {
        background-color: #2d2d2d !important;
        color: #e6e6e6 !important;
        border: 1px solid #404040 !important;
      }
    `;
    document.head.appendChild(style);
    document.body.classList.add('dark-mode-extension');
  } else {
    // Remove dark mode
    const style = document.querySelector('style');
    if (style && style.textContent.includes('dark-mode-extension')) {
      style.remove();
    }
    document.body.classList.remove('dark-mode-extension');
  }
})(); 