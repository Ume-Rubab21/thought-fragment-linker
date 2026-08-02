from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
app = (ROOT / 'frontend' / 'src' / 'App.jsx').read_text(encoding='utf-8')
page = (ROOT / 'frontend' / 'src' / 'pages' / 'Splash.jsx').read_text(encoding='utf-8')
css = (ROOT / 'frontend' / 'src' / 'pages' / 'Splash.css').read_text(encoding='utf-8')
image = ROOT / 'frontend' / 'src' / 'assets' / 'thoughtlinker-splash.png'

assert "import Splash from './pages/Splash'" in app
assert '<Route path="/" element={<Splash />} />' in app
assert "SPLASH_DURATION_MS = 3000" in page
assert "navigate('/login', { replace: true })" in page
assert "role=\"progressbar\"" in page
assert "thoughtlinker-splash__progress-fill" in page
assert "@keyframes thoughtlinker-progress-shine" in css
assert image.exists() and image.stat().st_size > 100_000

print('ANIMATED SPLASH HOME TEST PASSED')
