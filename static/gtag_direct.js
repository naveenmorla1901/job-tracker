// Direct implementation of Google Analytics for Streamlit
window.dataLayer = window.dataLayer || [];
function gtag(){window.dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', 'G-EGVJQG5M34');

// Create and add the script tag
var gtagScript = document.createElement('script');
gtagScript.async = true;
gtagScript.src = 'https://www.googletagmanager.com/gtag/js?id=G-EGVJQG5M34';
document.head.appendChild(gtagScript);

console.log("Google Analytics directly injected");