function DatePicker(date, nodeId, onSelect, usedDates = null, needPrevNext = true) {
    this.isRange = date.indexOf('-') != -1
    this.onSelect = onSelect
    this.usedDates = usedDates === null ? new Set() : new Set(usedDates)
    this.needPrevNext = needPrevNext

    this.weekDays = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    this.months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]

    this.picker = this.MakeNode("div", "date-picker", document.getElementById(nodeId))
    this.controls = this.MakeNode("div", "date-picker-controls", this.picker)
    this.calendar = this.MakeNode("div", "date-picker-calendar", this.picker)
    this.popup = this.MakeNode("div", "date-picker-popup", document.getElementsByTagName("body")[0])

    window.addEventListener('click', (e) => {
        if (!this.IsOpened())
            return

        let node = this.isRange ? this.picker.parentNode.parentNode : this.picker

        if (!node.contains(e.target)) {
            this.HideCalendar()
            e.stopPropagation()
        }
    })

    this.MakeControls(date)
    this.MakeCalendar()
    this.MakeIcons()
    this.SetDate(date)
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
    let curr

    if (date == "") {
        curr = new Date()
    }
    else {
        let [day, month, year] = date.split(".")
        curr = new Date(+year, +month - 1, +day)
    }

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
    if (match && this.ValidateDate(match.groups.day, match.groups.month, match.groups.year))
        return `${match.groups.day.padStart(2, '0')}.${match.groups.month.padStart(2, '0')}.${match.groups.year}`

    match = /^(?<day>\d\d?)\.(?<month>\d\d?)$/g.exec(value)
    if (match && this.ValidateDate(match.groups.day, match.groups.month, year))
        return `${match.groups.day.padStart(2, '0')}.${match.groups.month.padStart(2, '0')}.${year}`

    match = /^(?<day>\d\d?)$/g.exec(value)
    if (match && this.ValidateDate(match.groups.day, month, year))
        return `${match.groups.day.padStart(2, '0')}.${month.toString().padStart(2, '0')}.${year}`

    return null
}

DatePicker.prototype.FormatDate = function(date, day = null) {
    if (day === null)
        day = date.getDate().toString()

    date = new Date(date.getFullYear(), date.getMonth(), +day)

    day = date.getDate().toString()
    month = (date.getMonth() + 1).toString()
    year = date.getFullYear().toString()

    return `${day.padStart(2, '0')}.${month.padStart(2, '0')}.${year.padStart(2, '0')}`
}

DatePicker.prototype.IsCurrent = function(dates, day) {
    return !this.isRange && dates.start <= dates.curr && dates.curr <= dates.end && dates.curr.getDate() == day
}

DatePicker.prototype.IsToday = function(dates, day) {
    let today = new Date()
    let date = dates.start

    return today.getFullYear() == date.getFullYear() && today.getMonth() == date.getMonth() && today.getDate() == day
}

DatePicker.prototype.IsUsed = function(dates, day) {
    let date = this.FormatDate(dates.start, day)
    return this.usedDates.has(date)
}

DatePicker.prototype.CompareDates = function(date1, date2) {
    date1 = date1.split('.').reverse().join('.')
    date2 = date2.split('.').reverse().join('.')
    if (date1 < date2)
        return -1

    if (date1 > date2)
        return 1

    return 0
}

DatePicker.prototype.Reset = function() {
    if (this.isRange) {
        let startDate = this.FormatDate(this.startDate)
        let endDate = this.FormatDate(this.endDate)

        this.dates = this.GetCalendarDates(startDate)
        this.startDateInput.value = startDate
        this.endDateInput.value = endDate
        this.range = {start: startDate, end: endDate}

        this.startDateInput.classList.remove("error")
        this.startDateInput.blur()
        this.endDateInput.classList.remove("error")
        this.endDateInput.blur()
    }
    else {
        let date = this.FormatDate(this.initDate)
        this.dates = this.GetCalendarDates(date)
        this.currDateInput.value = date
        this.currDateInput.classList.remove("error")
        this.currDateInput.blur()
    }

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
    let date = this.dates.curr
    let day = date.getDate() + step
    this.onSelect(this.FormatDate(date, day))
}

DatePicker.prototype.ShowCalendar = function() {
    this.picker.classList.add("date-picker-opened")
    this.popup.classList.add("date-picker-popup-show")
    this.closeIcon.style.display = null

    if (this.isRange)
        this.applyIcon.style.display = null
}

DatePicker.prototype.HideCalendar = function() {
    this.picker.classList.remove("date-picker-opened")
    this.popup.classList.remove("date-picker-popup-show")
    this.closeIcon.style.display = "none"

    if (this.isRange)
        this.applyIcon.style.display = "none"

    this.Reset()
}

DatePicker.prototype.IsOpened = function() {
    return this.picker.classList.contains("date-picker-opened")
}

DatePicker.prototype.ShowOnFocus = function(input) {
    if (this.IsOpened())
        return

    input.blur()
    this.ShowCalendar()
}

DatePicker.prototype.RemoveErrorOnInput = function(input) {
    input.classList.remove("error")
}

DatePicker.prototype.ValidateInput = function() {
    let isCorrect = true

    if (this.isRange) {
        let startDate = this.ParseDate(this.startDateInput.value)
        let endDate = this.ParseDate(this.endDateInput.value)

        if (endDate === null) {
            this.endDateInput.classList.add("error")
            this.endDateInput.focus()
            isCorrect = false
        }

        if (this.ParseDate(startDate) === null) {
            this.startDateInput.classList.add("error")
            this.startDateInput.focus()
            isCorrect = false
        }

        if (isCorrect) {
            this.startDateInput.value = startDate
            this.endDateInput.value = endDate
            this.range = {start: startDate, end: endDate}
            this.FixRange()
        }
    }
    else {
        if (this.ParseDate(this.currDateInput.value) === null) {
            this.currDateInput.classList.add("error")
            this.currDateInput.focus()
            isCorrect = false
        }
    }

    return isCorrect
}

DatePicker.prototype.ValidateOnEnter = function(e) {
    if (e.keyCode != 13)
        return

    e.preventDefault()

    if (this.ValidateInput()) {
        this.onSelect(this.GetDate())
    }
}

DatePicker.prototype.FixRange = function() {
    if (this.CompareDates(this.range.start, this.range.end) <= 0)
        return

    this.endDateInput.value = this.range.start
    this.startDateInput.value = this.range.end
    this.range.start = this.startDateInput.value
    this.range.end = this.endDateInput.value
}

DatePicker.prototype.ClickOnDay = function(date) {
    if (!this.isRange) {
        this.currDateInput.value = date
        this.onSelect(this.GetDate())
        return
    }

    if (this.range.end !== null) {
        this.startDateInput.value = date
        this.endDateInput.value = date
        this.range = {start: date, end: null}
    }
    else {
        this.range.end = date
        this.endDateInput.value = date
        this.FixRange()
    }
}

DatePicker.prototype.ClickOnMonth = function() {
    this.range.start = this.FormatDate(this.dates.start)
    this.range.end = this.FormatDate(this.dates.end)
    this.startDateInput.value = this.range.start
    this.endDateInput.value = this.range.end

    if (!this.isRange)
        this.onSelect(this.GetDate())
}

DatePicker.prototype.MakeControls = function(dateValue) {
    let controlLeft = this.MakeNode("div", "date-picker-controls-cell date-picker-controls-cell-left", this.controls)
    let controlCenter = this.MakeNode("div", `date-picker-controls-cell date-picker-controls-cell-date${this.isRange ? " date-picker-controls-cell-range-date" : ""}`, this.controls)
    let controlRight = this.MakeNode("div", "date-picker-controls-cell date-picker-controls-cell-right", this.controls)

    this.prevMonth = this.MakeNode("span", "date-picker-control-icon date-picker-calendar-icon", controlLeft, {"innerHTML": "<span class='fa fa-angle-double-left'></span>"})
    this.prevMonth.addEventListener("click", () => this.StepMonth(-1))

    if (this.needPrevNext) {
        let prevDay = this.MakeNode("span", "date-picker-control-icon", controlLeft, {"innerHTML": "<span class='fa fa-angle-left'></span>"})
        prevDay.addEventListener("click", () => this.StepDay(-1))
    }

    if (this.isRange) {
        let [startDate, endDate] = dateValue.split('-')
        this.startDateInput = this.MakeNode("input", "date-picker-date-range", controlCenter, {"type": "text", "value": startDate, "inputmode": "decimal"})
        this.MakeNode("span", "", controlCenter, {"innerText": "-"})
        this.endDateInput = this.MakeNode("input", "date-picker-date-range", controlCenter, {"type": "text", "value": endDate, "inputmode": "decimal"})

        this.startDateInput.addEventListener('focus', () => this.ShowOnFocus(this.startDateInput))
        this.startDateInput.addEventListener("input", () => this.RemoveErrorOnInput(this.startDateInput))
        this.startDateInput.addEventListener("keydown", (e) => this.ValidateOnEnter(e))

        this.endDateInput.addEventListener('focus', () => this.ShowOnFocus(this.endDateInput))
        this.endDateInput.addEventListener("input", () => this.RemoveErrorOnInput(this.endDateInput))
        this.endDateInput.addEventListener("keydown", (e) => this.ValidateOnEnter(e))
    }
    else {
        this.currDateInput = this.MakeNode("input", "", controlCenter, {"type": "text", "value": dateValue, "inputmode": "decimal"})
        this.currDateInput.addEventListener('focus', () => this.ShowOnFocus(this.currDateInput))
        this.currDateInput.addEventListener("input", () => this.RemoveErrorOnInput(this.currDateInput))
        this.currDateInput.addEventListener("keydown", (e) => this.ValidateOnEnter(e))
    }

    if (this.needPrevNext) {
        let nextDay = this.MakeNode("span", "date-picker-control-icon", controlRight, {"innerHTML": "<span class='fa fa-angle-right'></span>"})
        nextDay.addEventListener("click", () => this.StepDay(1))
    }

    this.nextMonth = this.MakeNode("span", "date-picker-control-icon date-picker-calendar-icon", controlRight, {"innerHTML": "<span class='fa fa-angle-double-right'></span>"})
    this.nextMonth.addEventListener("click", () => this.StepMonth(1))
}

DatePicker.prototype.MakeIcons = function() {
    this.resetIcon = this.MakeNode("span", "date-picker-reset-icon fa fa-repeat", this.picker)
    this.resetIcon.style.display = "none"
    this.resetIcon.addEventListener("click", () => this.Reset())

    this.closeIcon = this.MakeNode("span", "date-picker-close-icon fa fa-times", this.picker)
    this.closeIcon.style.display = "none"
    this.closeIcon.addEventListener("click", () => this.HideCalendar())

    if (!this.isRange)
        return

    this.applyIcon = this.MakeNode("span", "date-picker-apply-icon fa fa-check", this.picker)
    this.applyIcon.style.display = "none"
    this.applyIcon.addEventListener("click", () => this.onSelect(this.GetDate()))
}

DatePicker.prototype.MakeCalendarCell = function() {
    let calendarCell = this.MakeNode("div", "date-picker-calendar-cell", this.calendarTable)
    let month = this.MakeNode("div", "date-picker-month", calendarCell)

    if (this.isRange)
        month.addEventListener("click", () => this.ClickOnMonth())

    let weekDays = this.MakeNode("div", "date-picker-week-days", calendarCell)

    for (let name of this.weekDays)
        this.MakeNode("div", "date-picker-week-day", weekDays, {"innerText": name})

    let calendarDays = this.MakeNode("div", "date-picker-calendar-days", calendarCell)
    return calendarCell
}

DatePicker.prototype.MakeCalendar = function() {
    this.calendarTable = this.MakeNode("div", "date-picker-calendar-table", this.calendar)
    this.calendarCellPrev = this.MakeCalendarCell()
    this.calendarCell = this.MakeCalendarCell()
    this.calendarCellNext = this.MakeCalendarCell()

    this.calendarTable.addEventListener('touchstart', (e) => this.CalendarTouchStart(e))
    this.calendarTable.addEventListener('touchmove', (e) => this.CalendarTouchMove(e))
    this.calendarTable.addEventListener('touchend', (e) => this.CalendarTouchEnd(e))
    this.calendarTable.addEventListener('transitionend', () => this.CalendarTransitionEnd())
}

DatePicker.prototype.CalendarTouchStart = function(e) {
    this.startX = e.touches[0].clientX
    this.calendarTable.style.transition = null
}

DatePicker.prototype.CalendarTouchMove = function(e) {
    let width = this.calendarTable.clientWidth
    this.deltaX = e.touches[0].clientX - this.startX
    this.calendarTable.style.transform = `translateX(${Math.max(-width / 3, Math.min(width / 3, this.deltaX)) - width / 3}px)`

    if (this.isRange) {
        this.startDateInput.blur()
        this.endDateInput.blur()
    }
    else {
        this.currDateInput.blur()
    }
}

DatePicker.prototype.CalendarTouchEnd = function(e) {
    let width = this.calendarTable.clientWidth
    this.position = Math.max(-1 / 3, Math.min(1 / 3, this.deltaX / width))

    if (this.position < -1/21)
        this.position = 1
    else if (this.position > 1/21)
        this.position = -1
    else
        this.position = 0

    let delta = (-this.position - 1) * width / 3

    this.calendarTable.style.transition = 'transform 0.15s'
    this.calendarTable.style.transform = `translateX(${delta}px)`
}

DatePicker.prototype.CalendarTransitionEnd = function() {
    this.calendarTable.style.transition = null
    this.deltaX = 0

    if (this.position == -1)
        this.StepMonth(-1)
    else if (this.position == 1)
        this.StepMonth(1)

    this.UpdateCalendar()
}

DatePicker.prototype.UpdateCalendarDays = function(calendarCell, dates) {
    let calendarDays = calendarCell.getElementsByClassName("date-picker-calendar-days")[0]
    let month = calendarCell.getElementsByClassName("date-picker-month")[0]

    calendarDays.innerHTML = ""
    month.innerText = `${this.months[dates.start.getMonth()]} ${dates.start.getFullYear()}`

    let day = 2 - dates.start.getDay()
    if (day == 2)
        day = -5

    let endDay = dates.end.getDate()
    let weekRow = null

    for (let index = 0; day <= endDay || index % 7 != 0; index++) {
        if (index % 7 == 0)
            weekRow = this.MakeNode("div", "date-picker-calendar-row", calendarDays)

        let dayDiv = this.MakeNode("div", "date-picker-calendar-day", weekRow)
        let daySpan = this.MakeNode("span", "date-picker-calendar-day-span", dayDiv, {"innerText": day > 0 && day <= endDay ? day : this.GetIncreasedDay(dates.start, day - 1)})
        let date = this.FormatDate(dates.start, day)

        if (!this.IsCurrent(dates, day)) {
            daySpan.addEventListener("click", (e) => {
                this.ClickOnDay(date)
                e.stopPropagation()
            })
        }

        if (day <= 0 || day > endDay)
            dayDiv.classList.add("date-picker-calendar-day-prev")
        if (this.IsCurrent(dates, day))
            dayDiv.classList.add("date-picker-calendar-day-current")
        if (this.IsToday(dates, day))
            dayDiv.classList.add("date-picker-calendar-day-today")

        if (this.IsUsed(dates, day))
            this.MakeNode("div", "date-picker-calendar-day-used", dayDiv, {"innerText": " "})

        if (this.isRange) {
            if (this.range.end === null) {
                if (this.range.start == date)
                    dayDiv.classList.add("date-picker-calendar-day-selected")
            }
            else if (this.CompareDates(this.range.start, date) <= 0 && this.CompareDates(date, this.range.end) <= 0) {
                dayDiv.classList.add("date-picker-calendar-day-selected")
            }

            if (date == this.range.start && (this.range.end == null || this.range.start == this.range.end))
                dayDiv.classList.add("date-picker-calendar-day-selected-start-end")
            else {
                if (date == this.range.start)
                    dayDiv.classList.add("date-picker-calendar-day-selected-start")

                if (date == this.range.end)
                    dayDiv.classList.add("date-picker-calendar-day-selected-end")
            }
        }

        day++
    }
}

DatePicker.prototype.UpdateCalendar = function() {
    let month = this.dates.start.getMonth() + 1
    let year = this.dates.start.getFullYear()

    this.calendarTable.style.transition = null
    this.calendarTable.style.transform = "translateX(-33.33%)"

    this.prevDates = this.GetCalendarDates(`1.${month - 1}.${year}`)
    this.prevDates.curr = this.dates.curr
    this.UpdateCalendarDays(this.calendarCellPrev, this.prevDates)

    this.UpdateCalendarDays(this.calendarCell, this.dates)

    this.nextDates = this.GetCalendarDates(`1.${month + 1}.${year}`)
    this.nextDates.curr = this.dates.curr
    this.UpdateCalendarDays(this.calendarCellNext, this.nextDates)
}

DatePicker.prototype.SetDate = function(date) {
    if (this.isRange) {
        let [startDate, endDate] = date.split('-')
        this.startDate = this.GetCalendarDates(startDate).curr
        this.endDate = this.GetCalendarDates(endDate).curr
        this.range = {start: startDate, end: endDate}
        this.dates = this.GetCalendarDates(endDate)
        this.startDateInput.value = this.range.start
        this.endDateInput.value = this.range.end
    }
    else {
        this.dates = this.GetCalendarDates(date)
        this.initDate = this.dates.curr
    }

    this.UpdateCalendar()
}

DatePicker.prototype.GetDate = function() {
    if (this.isRange)
        return `${this.ParseDate(this.startDateInput.value)}-${this.ParseDate(this.endDateInput.value)}`

    return this.ParseDate(this.currDateInput.value)
}