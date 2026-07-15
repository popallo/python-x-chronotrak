document.addEventListener("DOMContentLoaded", function () {
    const freq = document.getElementById("recurrence_frequency");
    const interval = document.getElementById("recurrence_interval");
    const startDate = document.getElementById("recurrence_start_date");
    const endType = document.getElementById("recurrence_end_type");
    const weekdays = document.getElementById("recurrence_weekdays_section");
    const businessDays = document.getElementById("recurrence_business_days_section");
    const endDateWrap = document.getElementById("recurrence_end_date_wrapper");
    const countWrap = document.getElementById("recurrence_count_wrapper");

    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");
    if (startDate && !startDate.value) {
        startDate.value = `${yyyy}-${mm}-${dd}`;
    }

    function refresh() {
        const enabled = freq && freq.value !== "none";
        if (interval) {
            interval.disabled = !enabled;
        }
        if (startDate) {
            startDate.disabled = !enabled;
        }
        if (endType) {
            endType.disabled = !enabled;
        }

        if (!enabled) {
            weekdays.classList.add("d-none");
            businessDays.classList.add("d-none");
            endDateWrap.classList.add("d-none");
            countWrap.classList.add("d-none");
            return;
        }

        weekdays.classList.toggle("d-none", freq.value !== "weekly");
        businessDays.classList.toggle("d-none", freq.value !== "daily");
        endDateWrap.classList.toggle("d-none", endType.value !== "until");
        countWrap.classList.toggle("d-none", endType.value !== "count");
    }

    if (freq) {
        freq.addEventListener("change", refresh);
    }
    if (endType) {
        endType.addEventListener("change", refresh);
    }
    refresh();
});
