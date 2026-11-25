(() => {
    const form = document.getElementById('category-form');
    if (!form) return;

    const input = document.getElementById('nombre');
    const submitButton = document.getElementById('category-submit');
    const cancelButton = document.getElementById('category-cancel');
    const list = document.querySelector('.canaco-admin-record-list');
    const feedback = document.getElementById('category-feedback');
    const createLabel = submitButton.textContent.trim();
    let editingCard = null;
    let isProcessing = false;

    function showMessage(message, type = 'danger') {
        feedback.textContent = '';
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.setAttribute('role', 'alert');
        alert.textContent = message;
        feedback.appendChild(alert);
    }

    function clearMessage() {
        feedback.textContent = '';
    }

    function setBusy(busy) {
        isProcessing = busy;
        form.querySelectorAll('button').forEach((button) => {
            button.disabled = busy;
        });
        list.querySelectorAll('button').forEach((button) => {
            button.disabled = busy;
        });
    }

    function resetForm() {
        editingCard = null;
        input.value = '';
        submitButton.textContent = createLabel;
        cancelButton.classList.add('d-none');
        form.action = form.dataset.createUrl || form.action;
        clearMessage();
    }

    async function send(url, values = {}) {
        const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]').value;
        const body = new URLSearchParams(values);
        const response = await fetch(url, {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
                'X-CSRFToken': csrfToken,
            },
            body,
        });

        let data;
        try {
            data = await response.json();
        } catch {
            throw new Error('El servidor devolvió una respuesta inesperada.');
        }

        if (!response.ok || !data.ok) {
            throw new Error(data.message || 'No se pudo completar la operación.');
        }
        return data;
    }

    function buildCard(category) {
        const card = document.createElement('article');
        card.className = 'canaco-admin-record-card';
        card.dataset.categoryId = category.id;
        card.dataset.editUrl = category.edit_url;
        card.dataset.deleteUrl = category.delete_url;

        const content = document.createElement('div');
        content.className = 'canaco-admin-record-content';
        const topline = document.createElement('div');
        topline.className = 'canaco-admin-record-topline';
        const label = document.createElement('span');
        label.className = 'canaco-admin-record-label';
        label.textContent = `Categoría #${category.id}`;
        topline.appendChild(label);

        const name = document.createElement('h3');
        name.className = 'canaco-admin-record-title';
        name.dataset.categoryName = '';
        name.textContent = category.nombre;

        const meta = document.createElement('div');
        meta.className = 'canaco-admin-record-meta';
        const created = document.createElement('span');
        created.textContent = `Creada el ${category.created_at}`;
        meta.appendChild(created);
        content.append(topline, name, meta);

        const actions = document.createElement('div');
        actions.className = 'canaco-admin-record-actions';
        const edit = document.createElement('button');
        edit.type = 'button';
        edit.className = 'btn btn-outline-secondary btn-sm';
        edit.dataset.categoryEdit = '';
        edit.textContent = 'Editar';
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'btn btn-sm canaco-comment-delete';
        remove.dataset.categoryDelete = '';
        remove.textContent = 'Eliminar';
        actions.append(edit, remove);
        card.append(content, actions);
        return card;
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (isProcessing) return;
        clearMessage();
        setBusy(true);
        try {
            const wasEditing = Boolean(editingCard);
            const url = wasEditing ? editingCard.dataset.editUrl : form.action;
            const data = await send(url, { nombre: input.value });
            const card = wasEditing ? editingCard : buildCard(data.categoria);
            card.querySelector('[data-category-name]').textContent = data.categoria.nombre;
            card.dataset.editUrl = data.categoria.edit_url;
            card.dataset.deleteUrl = data.categoria.delete_url;
            if (!editingCard) {
                list.querySelector('[data-category-empty]')?.remove();
                list.appendChild(card);
            }
            resetForm();
            showMessage(
                wasEditing ? 'Categoría actualizada correctamente.' : 'Categoría creada correctamente.',
                'success'
            );
        } catch (error) {
            showMessage(error.message);
        } finally {
            setBusy(false);
        }
    });

    list.addEventListener('click', async (event) => {
        const editButton = event.target.closest('[data-category-edit]');
        if (editButton) {
            if (isProcessing) return;
            editingCard = editButton.closest('[data-category-id]');
            input.value = editingCard.querySelector('[data-category-name]').textContent;
            submitButton.textContent = 'Actualizar';
            cancelButton.classList.remove('d-none');
            clearMessage();
            input.focus();
            return;
        }

        const deleteButton = event.target.closest('[data-category-delete]');
        if (!deleteButton || isProcessing) return;
        const card = deleteButton.closest('[data-category-id]');
        const categoryName = card.querySelector('[data-category-name]').textContent;
        if (!window.confirm(`¿Estás seguro de eliminar la categoría "${categoryName}"?`)) return;

        clearMessage();
        setBusy(true);
        try {
            await send(card.dataset.deleteUrl);
            const wasEditing = editingCard === card;
            card.remove();
            if (!list.querySelector('[data-category-id]')) {
                const empty = document.createElement('div');
                empty.className = 'canaco-news-empty';
                empty.dataset.categoryEmpty = '';
                empty.textContent = 'No hay categorías registradas.';
                list.appendChild(empty);
            }
            if (wasEditing) resetForm();
            showMessage('Categoría eliminada correctamente.', 'success');
        } catch (error) {
            showMessage(error.message);
        } finally {
            setBusy(false);
        }
    });

    cancelButton.addEventListener('click', resetForm);
})();
