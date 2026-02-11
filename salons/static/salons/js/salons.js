console.log('salons.js');

const sidebarToggle = document.getElementById('sidebarToggle');

if (sidebarToggle) {
	sidebarToggle.addEventListener('click', () => {
		const isCollapsed = document.body.classList.toggle('sidebar-collapsed');
		sidebarToggle.setAttribute('aria-expanded', String(!isCollapsed));
	});
}