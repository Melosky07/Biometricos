import React, { useState } from 'react'

const RegistroForm = ({ onRegistrar }) => {
    const [nombre, setNombre] = useState('')

    const handleSubmit = (e) => {
        e.preventDefault()
        onRegistrar(nombre)
        setNombre('')  // Limpiar el input
    }

    return (
        <form onSubmit={handleSubmit}>
            <input
                placeholder="Nombre"
                value={nombre}
                onChange={e => setNombre(e.target.value)}
                required
            />
            <button type="submit">Registrar</button>
        </form>
    )
}

export default RegistroForm
