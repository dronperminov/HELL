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
    return value.match(/^\d+(.\d+)?$/g)
}

function IsPositiveReal(value) {
    return value.match(/^\d+(.\d{0,2})?$/g) && +value > 0
}

function ValidateFields(fields) {
    let data = {}

    for (const field of fields) {
        const fieldBox = document.getElementById(field.name)
        const value = fieldBox.value

        if (field.func !== null && !field.func(value)) {
            alert(field.message)
            fieldBox.focus()
            return null
        }

        data[field.name] = value
    }

    return data
}

function MakeDiv(className, parent=null) {
    let div = document.createElement("div")
    div.className = className

    if (parent !== null)
        parent.appendChild(div)

    return div
}

function MakeInput(type, parent, attributes = null) {
    let input = document.createElement("input")
    input.type = type

    if (attributes !== null) {
        for (let attribute of Object.keys(attributes))
            input.setAttribute(attribute, attributes[attribute])
    }

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
