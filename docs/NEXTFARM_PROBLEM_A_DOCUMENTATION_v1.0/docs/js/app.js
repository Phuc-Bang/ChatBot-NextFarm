
const search = document.getElementById('search');
const sections = [...document.querySelectorAll('main section')];
search.addEventListener('input', () => {
  const q = search.value.trim().toLowerCase();
  sections.forEach(s => {
    const hit = !q || s.innerText.toLowerCase().includes(q);
    s.style.display = hit ? '' : 'none';
  });
});
