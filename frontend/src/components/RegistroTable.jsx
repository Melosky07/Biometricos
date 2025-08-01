import React from 'react'

const RegistrosTable = ({ registros }) => (
    <table border="1">
        <thead>
            <tr>
                <th>Nombre</th>
                <th>Fecha</th>
                <th>Hora Entrada</th>
                <th>Hora Salida</th>
            </tr>
        </thead>
        <tbody>
            {registros.map((reg, index) => (
                <tr key={index}>
                    <td>{reg.persona.nombre}</td>
                    <td>{reg.fecha}</td>
                    <td>{reg.hora_entrada}</td>
                    <td>{reg.hora_salida || '-'}</td>
                </tr>
            ))}
        </tbody>
    </table>
)

export default RegistrosTable