import React, { useState, useEffect } from 'react'
import axios from 'axios'
import RegistroForm from './RegistroFrom'
import RegistrosTable from './RegistroTable'

const API = 'http://localhost:8000/registros/'
const REPORT_URL = 'http://localhost:8000/reporte-excel/'

const RegistroAsistencia = () => {
    const [registros, setRegistros] = useState([])
    const [resumen, setResumen] = useState('')

    const fetchData = async () => {
        const res = await axios.get(API)
        const resumen = await axios.get(API + 'resumen_semanal/')
        setRegistros(res.data)
        setResumen(resumen.data.total_horas_semanales)
    }

    useEffect(() => { fetchData() }, [])

    const registrar = async (registro) => {
        await axios.post(API, registro)
        fetchData()
    }

    return (
        <div>
            <RegistroForm onRegistrar={registrar} />
            <button onClick={() => window.open(REPORT_URL)}>Descargar Excel</button>
            {/* <h3>{resumen}</h3> */}
            <RegistrosTable registros={registros} />
        </div>
    )
}

export default RegistroAsistencia
