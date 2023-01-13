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
        alert(error)
        throw error
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