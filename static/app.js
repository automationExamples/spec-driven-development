const listEl = document.getElementById("list");
const formEl = document.getElementById("insert-form");
const statusEl = document.getElementById("form-status");
const refreshBtn = document.getElementById("refresh");
let latestApplications = [];

async function fetchApplications() {
  const response = await fetch("/applications");
  if (!response.ok) {
    throw new Error("Failed to load applications");
  }
  return await response.json();
}

function renderList(applications) {
  if (!applications.length) {
    listEl.innerHTML = "<p class=\"empty\">No applications in queue.</p>";
    return;
  }

  const rows = applications
    .map(
      (item) => `
        <article class="row">
          <div class="rank-cell" data-id="${item.id}" data-position="${item.position}">
            <span class="rank-value">${item.position}</span>
            <div class="rank-actions">
              <button class="icon-button" type="button" data-action="move" aria-label="Edit rank">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 16.75V20h3.25L17.81 9.44l-3.25-3.25L4 16.75zm14.71-9.04a1.003 1.003 0 0 0 0-1.42l-1.99-1.99a1.003 1.003 0 0 0-1.42 0l-1.45 1.45 3.25 3.25 1.61-1.29z"/>
                </svg>
              </button>
              <button class="icon-button danger" type="button" data-action="delete" aria-label="Remove application">
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6 7h12l-1 14H7L6 7zm3-3h6l1 2H8l1-2zm-1 2h8v2H8V6z"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="content">
            <h3>${item.name}</h3>
            <p>${item.summary}</p>
          </div>
        </article>
      `
    )
    .join("");

  listEl.innerHTML = rows;
}

async function refreshList() {
  try {
    const data = await fetchApplications();
    latestApplications = data;
    renderList(data);
  } catch (error) {
    listEl.innerHTML = `<p class=\"error\">${error.message}</p>`;
  }
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  statusEl.textContent = "";

  const formData = new FormData(formEl);
  const payload = {
    name: formData.get("name").trim(),
    summary: formData.get("summary").trim(),
  };

  if (!payload.name || !payload.summary) {
    statusEl.textContent = "Name and summary are required.";
    return;
  }

  const positionValue = formData.get("position");
  const desiredPosition = positionValue ? Number.parseInt(positionValue, 10) : null;
  const maxPosition = latestApplications.length;

  let placementPayload = { ...payload, placement: "end" };
  if (desiredPosition !== null && Number.isFinite(desiredPosition)) {
    if (desiredPosition <= 1) {
      placementPayload = { ...payload, placement: "start" };
    } else if (desiredPosition > maxPosition) {
      placementPayload = { ...payload, placement: "end" };
    } else {
      const beforeItem = latestApplications.find(
        (item) => item.position === desiredPosition - 1
      );
      const afterItem = latestApplications.find(
        (item) => item.position === desiredPosition
      );
      if (beforeItem && afterItem) {
        placementPayload = {
          ...payload,
          placement: "between",
          before_id: beforeItem.id,
          after_id: afterItem.id,
        };
      } else {
        placementPayload = { ...payload, placement: "end" };
      }
    }
  }

  const response = await fetch("/applications/insert", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(placementPayload),
  });

  if (!response.ok) {
    const result = await response.json();
    statusEl.textContent = result.detail || "Failed to insert application.";
    return;
  }

  formEl.reset();
  statusEl.textContent = "Application added.";
  await refreshList();
});

refreshBtn.addEventListener("click", refreshList);

listEl.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof Element)) {
    return;
  }

  const actionButton = target.closest("button[data-action]");
  if (!actionButton) {
    return;
  }

  const rankCell = actionButton.closest(".rank-cell");
  if (!rankCell) {
    return;
  }

  const applicationId = Number(rankCell.dataset.id);
  const currentPosition = Number(rankCell.dataset.position);
  if (!Number.isFinite(applicationId) || !Number.isFinite(currentPosition)) {
    return;
  }

  const action = actionButton.dataset.action;
  if (action === "move") {
    const input = prompt("Enter new rank:", String(currentPosition));
    if (input === null) {
      return;
    }

    const newPosition = Number.parseInt(input, 10);
    if (!Number.isFinite(newPosition)) {
      statusEl.textContent = "Rank must be a whole number.";
      return;
    }

    const maxPosition = latestApplications.length || currentPosition;
    const clampedPosition = Math.min(Math.max(newPosition, 1), maxPosition);

    if (clampedPosition === currentPosition) {
      statusEl.textContent = "Rank unchanged.";
      return;
    }

    const response = await fetch(`/applications/${applicationId}/move`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ new_position: clampedPosition }),
    });

    if (!response.ok) {
      const result = await response.json();
      statusEl.textContent = result.detail || "Failed to move application.";
      return;
    }

    statusEl.textContent = "Rank updated.";
    await refreshList();
  }

  if (action === "delete") {
    const confirmed = confirm("Remove this application from the queue?");
    if (!confirmed) {
      return;
    }

    const response = await fetch(`/applications/${applicationId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const result = await response.json();
      statusEl.textContent = result.detail || "Failed to remove application.";
      return;
    }

    statusEl.textContent = "Application removed.";
    await refreshList();
  }
});

refreshList();
