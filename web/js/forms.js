async function SendRequest(url, data = null) {
    try {
        let params = {
            method: data == null ? 'GET' : 'POST',
            mode: 'cors',
            cache: 'no-cache',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json'
            },
            redirect: 'follow',
            referrerPolicy: 'no-referrer'
        }

        if (data != null)
            params.body = JSON.stringify(data)

        const response = await fetch(url, params)
        return await response.json()
    }
    catch (error) {
        return {"status": "fail", "message": error}
    }
}

function IsNotEmptyValue(value) {
    return !value.match(/^\s*$/g)
}

function IsRealValue(value) {
    return value.match(/^\d+(\.\d+)?$/g) !== null
}

function IsPositiveReal(value) {
    return value.match(/^\d+(\.\d{0,2})?$/g) !== null && +value > 0
}

function GetInvalidMealTypeNameChars(name) {
    let chars = [...name.matchAll(/[.,!?<>{}\[\]"'&#]/g)].map((c) => c[0])
    chars = [...new Set(chars)]
    return chars
}

function SetAttributes(container, attributes) {
    if (attributes === null)
        return

    for (let attribute of Object.keys(attributes)) {
        if (attribute === "innerHTML")
            container.innerHTML = attributes[attribute]
        else if (attribute == "innerText")
            container.innerText = attributes[attribute]
        else
            container.setAttribute(attribute, attributes[attribute])
    }
}

function MakeDiv(className, parent=null, attributes = null, tagName = "div") {
    let div = document.createElement(tagName)
    div.className = className

    if (parent !== null)
        parent.appendChild(div)

    SetAttributes(div, attributes)

    return div
}

function MakeInput(type, parent, attributes = null) {
    let input = document.createElement("input")
    input.type = type

    SetAttributes(input, attributes)
    parent.appendChild(input)
    return input
}

function MakeIcon(parent, className, onclick = null) {
    let icon = document.createElement("button")
    let iconSpan = document.createElement("span")

    iconSpan.className = className
    icon.appendChild(iconSpan)
    parent.appendChild(icon)

    if (onclick !== null)
        icon.addEventListener("click", onclick)

    return icon
}

function CompareDates(date1, date2) {
    date1 = date1.split('.').reverse().join('.')
    date2 = date2.split('.').reverse().join('.')

    if (date1 < date2)
        return -1

    if (date1 > date2)
        return 1

    return 0
}

function ValidateDate(day, month, year) {
    let days = new Date(year, month, 0).getDate()
    return day >= 1 && day <= days && month >= 1 && month <= 12
}

function ParseDate(value) {
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

function FormatDate(day, month, year) {
    if (month == 0) {
        month = 12
        year--
    }

    return `${day.toString().padStart(2, '0')}.${month.toString().padStart(2, '0')}.${year}`
}

function ValidateInterval(startDate, endDate) {
    let start = startDate.split('.').reverse().join('.')
    let end = endDate.split('.').reverse().join('.')
    return start <= end
}
