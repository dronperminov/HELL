function DatePicker(date, nodeId, onSelect, usedDates = null) {
    this.onSelect = onSelect
    this.usedDates = usedDates === null ? new Set() : new Set(usedDates)

    this.weekDays = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    this.months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

    this.dates = this.GetCalendarDates(date)
    this.initDate = this.dates.curr

    this.picker = this.MakeNode("div", "date-picker", document.getElementById(nodeId))
    this.controls = this.MakeNode("div", "date-picker-controls", this.picker)
    this.calendar = this.MakeNode("div", "date-picker-calendar", this.picker)
    this.popup = this.MakeNode("div", "date-picker-popup", document.getElementsByTagName("body")[0])

    window.addEventListener('click', (e) => {   
        if (!this.picker.contains(e.target))
            this.HideCalendar()
    })

    this.MakeControls(date)
    this.MakeCalendar()
}

DatePicker.prototype.SetAttributes = function(node, attributes) {
    if (node === null)
        return

    for (let attribute of Object.keys(attributes)) {
        if (attribute === "innerHTML")
            node.innerHTML = attributes[attribute]
        else if (attribute == "innerText")
            node.innerText = attributes[attribute]
        else
            node.setAttribute(attribute, attributes[attribute])
    }
}

DatePicker.prototype.MakeNode = function(tagName, className, parent = null, attributes = null) {
    let node = document.createElement(tagName)
    node.className = className

    SetAttributes(node, attributes)

    if (parent !== null)
        parent.appendChild(node)

    return node
}

DatePicker.prototype.GetCalendarDates = function(date) {
    let [day, month, year] = date.split(".")
    let curr = new Date(+year, +month - 1, +day)

    month = curr.getMonth()
    year = curr.getFullYear()

    let start = new Date(year, month, 1)
    let end = new Date(year, month + 1, 0)

    return {start, curr, end}
}

DatePicker.prototype.GetIncreasedDay = function(date, days) {
    let day = date.getDate() + days
    let month = date.getMonth()
    let year = date.getFullYear()
    return new Date(year, month, day).getDate()
}

DatePicker.prototype.ValidateDate = function(day, month, year) {
    let days = new Date(year, month, 0).getDate()
    return day >= 1 && day <= days && month >= 1 && month <= 12
}

DatePicker.prototype.ParseDate = function(value) {
    let today = new Date()
    let year = today.getFullYear()
    let month = today.getMonth() + 1

    let match = /^(?<day>\d\d?)\.(?<month>\d\d?)\.(?<year>\d\d\d\d)$/g.exec(value)
    if (match && ValidateDate(match.groups.day, match.groups.month, match.groups.year))
        return `${match.groups.day.padStart(2, '0')}.${match.groups.month.padStart(2, '0')}.${match.groups.year}`

    match = /^(?<day>\d\d?)\.(?<month>\d\d?)$/g.exec(value)
    if (match && ValidateDate(match.groups.day, match.groups.month, year))
        return `${match.groups.day.padStart(2, '0')}.${match.groups.month.padStart(2, '0')}.${year}`

    match = /^(?<day>\d\d?)$/g.exec(value)
    if (match && ValidateDate(match.groups.day, month, year))
        return `${match.groups.day.padStart(2, '0')}.${month.toString().padStart(2, '0')}.${year}`

    return null
}

DatePicker.prototype.FormatDate = function(date, day = null) {
    if (day === null)
        day = date.getDate().toString()

    let month = (date.getMonth() + 1).toString()
    let year = date.getFullYear().toString()

    return `${day.padStart(2, '0')}.${month.padStart(2, '0')}.${year.padStart(2, '0')}`
}

DatePicker.prototype.InputDate = function(dateInput) {
    let date = this.ParseDate(dateInput.value)

    if (date === null) {
        dateInput.classList.add("error")
        dateInput.focus()
        return
    }

    this.onSelect(date)
}

DatePicker.prototype.IsCurrent = function(day) {
    return this.dates.start <= this.dates.curr && this.dates.curr <= this.dates.end && this.dates.curr.getDate() == day
}

DatePicker.prototype.IsToday = function(day) {
    let today = new Date()
    let date = this.dates.start

    return today.getFullYear() == date.getFullYear() && today.getMonth() == date.getMonth() && today.getDate() == day
}

DatePicker.prototype.IsUsed = function(day) {
    let date = this.FormatDate(this.dates.start, day + '')
    return this.usedDates.has(date)
}

DatePicker.prototype.Reset = function() {
    let date = this.FormatDate(this.initDate)
    this.dates = this.GetCalendarDates(date)
    this.resetIcon.style.display = "none"
    this.UpdateCalendar()
}

DatePicker.prototype.StepMonth = function(step) {
    let month = this.dates.start.getMonth() + step
    let year = this.dates.start.getFullYear()

    this.dates.start = new Date(year, month, 1)
    this.dates.end = new Date(year, month + 1, 0)
    this.dates.curr = this.initDate
    this.resetIcon.style.display = null
    this.UpdateCalendar()
}

DatePicker.prototype.StepDay = function(step) {
    let day = this.dates.curr.getDate() + step
    let month = this.dates.curr.getMonth() + 1
    let year = this.dates.curr.getFullYear()
    let curr = this.GetCalendarDates(`${day}.${month}.${year}`).curr

    this.onSelect(this.FormatDate(curr))
}

DatePicker.prototype.ToggleCalendar = function() {
    this.picker.classList.toggle("date-picker-opened")
    this.popup.classList.toggle("date-picker-popup-show")
}

DatePicker.prototype.ShowCalendar = function() {
    this.picker.classList.add("date-picker-opened")
    this.popup.classList.add("date-picker-popup-show")
}

DatePicker.prototype.HideCalendar = function() {
    this.picker.classList.remove("date-picker-opened")
    this.popup.classList.remove("date-picker-popup-show")
    this.Reset()
}

DatePicker.prototype.MakeControls = function(dateValue) {
    let controlLeft = this.MakeNode("div", "date-picker-controls-cell date-picker-controls-cell-left", this.controls)
    let controlCenter = this.MakeNode("div", "date-picker-controls-cell date-picker-controls-cell-date", this.controls)
    let controlRight = this.MakeNode("div", "date-picker-controls-cell date-picker-controls-cell-right", this.controls)

    this.prevMonth = this.MakeNode("span", "date-picker-control-icon date-picker-calendar-icon", controlLeft, {"innerHTML": "<span class='fa fa-angle-double-left'></span>"})
    this.prevMonth.addEventListener("click", () => this.StepMonth(-1))
    
    this.prevDay = this.MakeNode("span", "date-picker-control-icon", controlLeft, {"innerHTML": "<span class='fa fa-angle-left'></span>"})
    this.prevDay.addEventListener("click", () => this.StepDay(-1))

    this.currDateInput = this.MakeNode("input", "", controlCenter, {"type": "text", "value": dateValue, "inputmode": "decimal"})
    this.currDateInput.addEventListener("focus", () => this.ShowCalendar())
    this.currDateInput.addEventListener("input", () => {this.currDateInput.classList.remove("error")})

    this.currDateInput.addEventListener("keydown", (e) => {
        if (e.keyCode == 13) {
            e.preventDefault()
            this.InputDate(this.currDateInput)
        }
    })

    this.nextDay = this.MakeNode("span", "date-picker-control-icon", controlRight, {"innerHTML": "<span class='fa fa-angle-right'></span>"})
    this.nextDay.addEventListener("click", () => this.StepDay(1))

    this.nextMonth = this.MakeNode("span", "date-picker-control-icon date-picker-calendar-icon", controlRight, {"innerHTML": "<span class='fa fa-angle-double-right'></span>"})
    this.nextMonth.addEventListener("click", () => this.StepMonth(1))
}

DatePicker.prototype.UpdateCalendar = function() {
    this.month.innerText = `${this.months[this.dates.start.getMonth()]} ${this.dates.start.getFullYear()}`
    this.calendarDays.innerHTML = ""

    let day = 2 - this.dates.start.getDay()
    if (day == 2)
        day = -5

    let endDay = this.dates.end.getDate()
    let weekRow = null

    for (let index = 0; day <= endDay || index % 7 != 0; index++) {
        if (index % 7 == 0)
            weekRow = this.MakeNode("div", "date-picker-calendar-row", this.calendarDays)

        let dayDiv = this.MakeNode("div", "date-picker-calendar-day", weekRow)
        let daySpan = this.MakeNode("span", "date-picker-calendar-day-span", dayDiv, {"innerText": day > 0 && day <= endDay ? day : this.GetIncreasedDay(this.dates.start, day - 1)})

        if (day > 0 && !this.IsCurrent(day)) {
            let date = this.FormatDate(this.dates.start, day.toString())
            daySpan.addEventListener("click", () => this.onSelect(date))
        }

        if (day <= 0 || day > endDay)
            dayDiv.classList.add("date-picker-calendar-day-prev")
        if (this.IsCurrent(day))
            dayDiv.classList.add("date-picker-calendar-day-current")
        if (this.IsToday(day))
            dayDiv.classList.add("date-picker-calendar-day-today")
        if (this.IsUsed(day))
            dayDiv.classList.add("date-picker-calendar-day-used")

        day++
    }
}

DatePicker.prototype.MakeCalendar = function() {
    this.calendar.innerHTML = ""
    this.resetIcon = this.MakeNode("span", "date-picker-reset-icon fa fa-repeat", this.calendar)
    this.resetIcon.style.display = "none"
    this.resetIcon.addEventListener("click", () => this.Reset())

    this.month = this.MakeNode("div", "date-picker-month", this.calendar)

    let weekDays = this.MakeNode("div", "date-picker-week-days", this.calendar)

    for (let name of this.weekDays)
        this.MakeNode("div", "date-picker-week-day", weekDays, {"innerText": name})

    this.calendarDays = this.MakeNode("div", "date-picker-calendar-days", this.calendar)
    this.UpdateCalendar()
}
