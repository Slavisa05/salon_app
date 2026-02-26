const salonCards = document.querySelectorAll('.clickable-card[data-url]');

if (salonCards.length) {
	salonCards.forEach((card) => {
		const targetUrl = card.dataset.url;
		if (!targetUrl) {
			return;
		}

		card.addEventListener('click', () => {
			window.location.href = targetUrl;
		});

		card.addEventListener('keydown', (event) => {
			if (event.key === 'Enter' || event.key === ' ') {
				event.preventDefault();
				window.location.href = targetUrl;
			}
		});
	});
}

const bookingRoot = document.getElementById('booking-form-root');
if (bookingRoot) {
	const slotsUrl = bookingRoot.dataset.slotsUrl;
	const dateInput = document.getElementById('booking-date');
	const slotSelect = document.getElementById('slot');
	const submitBtn = document.getElementById('book-submit');

	const setSlots = (slots) => {
		slotSelect.innerHTML = '';

		if (!slots.length) {
			const option = document.createElement('option');
			option.value = '';
			option.textContent = 'Nema slobodnih termina za izabrani datum';
			slotSelect.appendChild(option);
			slotSelect.disabled = true;
			submitBtn.disabled = true;
			return;
		}

		const placeholder = document.createElement('option');
		placeholder.value = '';
		placeholder.textContent = 'Izaberite termin';
		slotSelect.appendChild(placeholder);

		slots.forEach((slot) => {
			const option = document.createElement('option');
			option.value = slot.id ? slot.id : '';                
			option.textContent = slot.label;
			if (!slot.id) { // virtuelni slot
				option.dataset.beginTime = slot.begin_time;
				option.dataset.endTime = slot.end_time;
				option.dataset.date = dateInput?.value;
			}
			slotSelect.appendChild(option);
		});

		slotSelect.addEventListener('change', function() {
			const selectedOption = slotSelect.options[slotSelect.selectedIndex];
			const beginInput = document.getElementById('slot-begin-time');
			const endInput = document.getElementById('slot-end-time');
			const dateInputHidden = document.getElementById('slot-date');

			if (selectedOption.value && selectedOption.value !== "null") {
				// Odabrali smo slot iz baze, obriši begin/end/date
				beginInput.value = '';
				endInput.value = '';
				dateInputHidden.value = '';
			} else {
				// Virtuelni slot
				beginInput.value = selectedOption.dataset.beginTime || '';
				endInput.value = selectedOption.dataset.endTime || '';
				dateInputHidden.value = selectedOption.dataset.date || dateInput.value;
			}
		});

		slotSelect.disabled = false;
		submitBtn.disabled = false;
	};

	const setLoading = () => {
		slotSelect.innerHTML = '';
		const option = document.createElement('option');
		option.value = '';
		option.textContent = 'Učitavanje termina...';
		slotSelect.appendChild(option);
		slotSelect.disabled = true;
		submitBtn.disabled = true;
	};

	const setError = () => {
		slotSelect.innerHTML = '';
		const option = document.createElement('option');
		option.value = '';
		option.textContent = 'Greška pri učitavanju termina';
		slotSelect.appendChild(option);
		slotSelect.disabled = true;
		submitBtn.disabled = true;
	};

	const loadSlots = async () => {
		const dateValue = dateInput?.value;
		if (!slotsUrl || !dateValue) {
			setError();
			return;
		}

		setLoading();

		try {
			const response = await fetch(`${slotsUrl}?date=${dateValue}`);
			if (!response.ok) {
				throw new Error('Failed to fetch slots');
			}

			const data = await response.json();
			setSlots(data.slots || []);
		} catch (error) {
			console.error(error);
			setError();
		}
	};

	if (dateInput) {
		dateInput.addEventListener('change', loadSlots);
	}

	loadSlots();
}