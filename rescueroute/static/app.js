let currentEvent = null;

const $ = (id) => document.getElementById(id);
const actionLabels = {
  event_created: ["Donation understood", "Rescue event created from donor input"],
  eligibility_checked: ["Safety & eligibility checked", "Allergen, refrigeration, hours and policy rules enforced"],
  allocation_optimized: ["Allocation optimized", "Eligible capacity matched to estimated meals"],
  volunteer_assigned: ["Volunteer assigned", "Route coverage confirmed"],
  notifications_generated: ["Parties notified", "Donor, recipients and volunteer messages prepared"],
  volunteer_cancelled: ["Volunteer cancelled", "Operational disruption detected"],
  recovered_with_replacement_volunteer: ["Autonomous recovery", "Replacement volunteer assigned without human intervention"],
  recovered_by_recipient_self_pickup: ["Autonomous recovery", "Recipients switched to self-pickup"],
  logistics_escalated_to_human: ["Escalated safely", "No safe autonomous logistics recovery remained"],
  human_approval: ["Human decision recorded", "Workflow resumed after explicit approval"],
  no_volunteer_available: ["No volunteer available", "Recovery path required"]
};

const presets = {
  standard: { donor:"ABC Bakery", sandwiches:42, bread:18, deadline:"20:30", nuts:false, cold:false },
  allergen: { donor:"Nut & Grain Cafe", sandwiches:55, bread:10, deadline:"20:30", nuts:true, cold:false },
  capacity: { donor:"Convention Center", sandwiches:150, bread:0, deadline:"20:00", nuts:false, cold:false }
};

document.querySelectorAll("[data-preset]").forEach((button) => {
  button.addEventListener("click", () => {
    const p = presets[button.dataset.preset];
    $("donor").value = p.donor;
    $("sandwiches").value = p.sandwiches;
    $("bread").value = p.bread;
    $("deadline").value = p.deadline;
    $("nuts").checked = p.nuts;
    $("cold").checked = p.cold;
  });
});

function render(event) {
  currentEvent = event;
  $("emptyState").classList.add("hidden");
  $("eventView").classList.remove("hidden");
  $("eventBadge").textContent = event.event_id;
  $("mealsMetric").textContent = event.estimated_meals - event.unallocated_meals;
  $("recipientMetric").textContent = event.allocation.length;
  $("humanMetric").textContent = event.human_approval_required ? "1" : "0";
  $("statusMetric").textContent = event.status.replaceAll("_", " ");

  $("timeline").innerHTML = event.audit.map((item) => {
    const label = actionLabels[item.action] || [item.action.replaceAll("_", " "), "Workflow action recorded"];
    const time = new Date(item.at).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit", second:"2-digit"});
    return `<div class="step"><div class="icon">✓</div><div><strong>${label[0]}</strong><p>${label[1]}</p></div><time>${time}</time></div>`;
  }).join("");

  if (event.human_approval_required) {
    $("approvalBox").classList.remove("hidden");
    $("approvalReason").textContent = event.approval_reason || "Human judgment required.";
  } else {
    $("approvalBox").classList.add("hidden");
  }
}

async function api(path, options={}) {
  const response = await fetch(path, {headers:{"Content-Type":"application/json"}, ...options});
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

$("rescueForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const button = e.currentTarget.querySelector("button[type=submit]");
  button.disabled = true; button.textContent = "Coordinating…";
  try {
    const event = await api("/api/rescues", {method:"POST", body:JSON.stringify({
      donor_name: $("donor").value,
      sandwiches: Number($("sandwiches").value),
      bread_loaves: Number($("bread").value),
      pickup_deadline: $("deadline").value,
      contains_nuts: $("nuts").checked,
      requires_refrigeration: $("cold").checked,
      mode: $("mode").value
    })});
    render(event);
  } catch (err) { alert(err.message); }
  finally { button.disabled = false; button.innerHTML = "Coordinate rescue <b>→</b>"; }
});

$("cancelBtn").addEventListener("click", async () => {
  if (!currentEvent) return;
  try {
    const result = await api(`/api/rescues/${currentEvent.event_id}/cancel-volunteer`, {method:"POST", body:"{}"});
    render(result.event);
  } catch (err) { alert(err.message); }
});


$("exhaustBtn").addEventListener("click", async () => {
  if (!currentEvent) return;
  try {
    const result = await api(`/api/demo/rescues/${currentEvent.event_id}/force-logistics-escalation`, {method:"POST", body:"{}"});
    render(result.event);
  } catch (err) { alert(err.message); }
});

$("approveBtn").addEventListener("click", async () => {
  if (!currentEvent) return;
  try {
    const result = await api(`/api/rescues/${currentEvent.event_id}/approve`, {method:"POST", body:JSON.stringify({note:"Approved in RescueRoute command center"})});
    render(result.event);
  } catch (err) { alert(err.message); }
});

$("resetBtn").addEventListener("click", async () => {
  await api("/api/reset", {method:"POST", body:"{}"});
  currentEvent = null;
  $("eventView").classList.add("hidden");
  $("emptyState").classList.remove("hidden");
  $("eventBadge").textContent = "NO ACTIVE EVENT";
});
