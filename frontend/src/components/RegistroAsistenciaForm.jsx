import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './RegistroAsistencia.css';

const API_BASE = import.meta.env.VITE_API_URL;

const API = `${API_BASE}/registros/`;
const SEARCH_URL = `${API_BASE}/buscar-persona/`;
const REPORT_URL = `${API_BASE}/reporte-excel/`;
const AUSENTES_URL = `${API_BASE}/reporte-ausentes/`;
const AUSENCIAS_SEMANA_URL = `${API_BASE}/reporte-ausencias-semanal/`;
const AUSENCIAS_HISTORICO_URL = `${API_BASE}/reporte-ausencias-historico/`;

const RegistroAsistencia = () => {
    const [nit, setNit] = useState('');
    const [nombre, setNombre] = useState('');
    const [dependencia, setDependencia] = useState('');
    const [cargo, setCargo] = useState('');
    const [mensaje, setMensaje] = useState('');
    const [error, setError] = useState('');
    const [registros, setRegistros] = useState([]);
    const [resumen, setResumen] = useState('');
    const [miniVista, setMiniVista] = useState([]);
    const [buscando, setBuscando] = useState(false);
    
    // ✅ Variables para detectar escaneo de código de barras
    const [lastKeyTime, setLastKeyTime] = useState(0);
    const [inputBuffer, setInputBuffer] = useState('');
    const [isScanning, setIsScanning] = useState(false);

    // ✅ Cargar datos iniciales
    const fetchData = async () => {
        try {
            const res = await axios.get(API);
            setRegistros(res.data);

            const resumenData = await axios.get('/api/asistencia/')
                .catch(() => ({ data: { total_horas_semanales: 'No disponible' } }));

            setResumen(resumenData.data.total_horas_semanales);
        } catch (err) {
            setError('Error al cargar datos');
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    // ✅ Debounce para la búsqueda automática (solo para entrada manual)
    useEffect(() => {
        if (nit && nit.length >= 3 && !isScanning) {
            setBuscando(true);
            setError('');
            
            const timeoutId = setTimeout(() => {
                buscarPersona(nit);
            }, 100);

            return () => {
                clearTimeout(timeoutId);
                setBuscando(false);
            };
        } else if (!isScanning) {
            setNombre('');
            setDependencia('');
            setCargo('');
            setError('');
            setBuscando(false);
        }
    }, [nit, isScanning]);

    // ✅ Detectar entrada de código de barras y procesamiento automático
    useEffect(() => {
        if (isScanning && nit && nit.length >= 6) {
            // Cuando se detecta un escaneo completo, procesar automáticamente
            const timeoutId = setTimeout(() => {
                buscarPersonaYRegistrar(nit);
                setIsScanning(false);
            }, 100); // Pequeña pausa para asegurar que se capture todo el código

            return () => clearTimeout(timeoutId);
        }
    }, [nit, isScanning]);

    // ✅ Función para buscar persona y registrar automáticamente
    const buscarPersonaYRegistrar = async (nitValue) => {
        setBuscando(true);
        setError('');
        
        try {
            // Primero buscar la información de la persona
            const response = await axios.get(`${SEARCH_URL}`, { params: { NIT: nitValue } });
            setNombre(response.data.Nombre || '');
            setDependencia(response.data.Dependencia || '');
            setCargo(response.data.Cargo || '');
            
            // Si se encontró la persona, registrar automáticamente
            if (response.data.Nombre) {
                await registrarAsistenciaAutomatico(nitValue);
            }
        } catch (err) {
            setError(err.response?.data?.error || 'No se encontró información para el NIT ingresado');
            setNombre('');
            setDependencia('');
            setCargo('');
        } finally {
            setBuscando(false);
        }
    };

    // ✅ Función para registrar asistencia automáticamente
    const registrarAsistenciaAutomatico = async (nitValue) => {
        try {
            const response = await axios.post(API, { NIT: nitValue });
            setMensaje(response.data.mensaje);
            setRegistros(response.data.registros);

            const ultimoRegistro = response.data.registros.filter(reg => reg.nit === nitValue).slice(-1)[0];
            if (ultimoRegistro) {
                setMiniVista([ultimoRegistro]);
            }

            // Limpiar campos después de 3 segundos para el próximo escaneo
            setTimeout(() => {
                setNit('');
                setNombre('');
                setDependencia('');
                setCargo('');
                setMensaje('');
                setError('');
            }, 500);
        } catch (error) {
            setError(`Error: ${error.response?.data?.detail || 'Error al registrar'}`);
        }
    };

    // ✅ Buscar información por NIT (solo búsqueda)
    const buscarPersona = async (nit) => {
        if (!nit.trim()) {
            setError('El NIT es obligatorio');
            setBuscando(false);
            return;
        }

        try {
            const response = await axios.get(`${SEARCH_URL}`, { params: { NIT: nit } });
            setNombre(response.data.Nombre || '');
            setDependencia(response.data.Dependencia || '');
            setCargo(response.data.Cargo || '');
            setError('');
        } catch (err) {
            if (nit.length > 6) {
                setError(err.response?.data?.error || 'No se encontró información para el NIT ingresado');
            }
            setNombre('');
            setDependencia('');
            setCargo('');
        } finally {
            setBuscando(false);
        }
    };

    // ✅ Registrar asistencia manual
    const enviarRegistroAsistencia = async () => {
        setMensaje('');
        setError('');

        if (!nit.trim()) {
            setError('El NIT es obligatorio');
            return;
        }

        try {
            const response = await axios.post(API, { NIT: nit });
            setMensaje(response.data.mensaje);
            setRegistros(response.data.registros);

            const ultimoRegistro = response.data.registros.filter(reg => reg.nit === nit).slice(-1)[0];
            if (ultimoRegistro) {
                setMiniVista([ultimoRegistro]);
            }

            setNit('');
            setNombre('');
            setDependencia('');
            setCargo('');
        } catch (error) {
            setError(`Error: ${error.response?.data?.detail || 'Error al registrar'}`);
        }
    };

    // ✅ Manejar cambios en el input con detección de código de barras
    const handleNitChange = (e) => {
        const value = e.target.value;
        const currentTime = Date.now();
        
        // Detectar si es entrada rápida (código de barras)
        if (currentTime - lastKeyTime < 50 && value.length > nit.length) {
            setIsScanning(true);
        }
        
        setLastKeyTime(currentTime);
        setNit(value);
        
        // Reset del buffer para detectar patrones de escaneo
        setInputBuffer(value);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        enviarRegistroAsistencia();
    };

    // ✅ Descargar reporte en Excel
    const descargarExcel = () => {
        window.open(REPORT_URL, '_blank');
    };

    const descargarAusentes = () => {
        window.open(AUSENTES_URL, '_blank');
    };

    const descargarAusenciasSemanales = () => {
        window.open(AUSENCIAS_SEMANA_URL, '_blank');
    };

    const descargarAusenciasHistorico = () => {
        window.open(AUSENCIAS_HISTORICO_URL, '_blank');
    };

    return (
        <div className="container">
            <div className="form-container">
                {/* <h1>ELABORADO SEBASTIAN DAVID MELO DIAZ </h1> */}
                <h2>Registro de Asistencia</h2>
                <form onSubmit={handleSubmit} className="form">
                    <div className="input-container">
                        <input
                            type="text"
                            placeholder="Ingrese el NIT o use el lector de código de barras"
                            value={nit}
                            onChange={handleNitChange}
                            className="input"
                            autoFocus
                        />
                        {buscando && (
                            <div className="loading-indicator">
                                <span>{isScanning ? 'Procesando código de barras...' : 'Buscando...'}</span>
                            </div>
                        )}
                        {isScanning && (
                            <div className="scanning-indicator">
                                <span>📱 Código de barras detectado</span>
                            </div>
                        )}
                    </div>

                    {/* Mostrar información del empleado si se encontró
                    {nombre && (
                        <div className="employee-info">
                            <p><strong>Nombre:</strong> {nombre}</p>
                            <p><strong>Cargo:</strong> {cargo}</p>
                            <p><strong>Dependencia:</strong> {dependencia}</p>
                        </div>
                    )} */}

                    <button 
                        type="submit" 
                        className="button" 
                        disabled={!nombre || isScanning}
                    >
                        {isScanning ? 'Procesando...' : `Registrar ${nombre ? 'Asistencia' : ''}`}
                    </button>
                </form>

                {mensaje && <p className="success">{mensaje}</p>}
                {error && <p className="error">{error}</p>}

                {/* <button onClick={descargarExcel} className="download-button">
                    Descargar Reporte Excel
                </button> */}

                {/* <button onClick={descargarAusentes} className="download-button">
                    Descargar Ausentes (Hoy)
                </button> */}

                

            </div>

            {/* ✅ Tabla completa */}
            <div className="table-container">
                <table className="table">
                    <thead>
                        <tr>
                            <th>Nombre</th>
                            <th>Fecha</th>
                            <th>Hora Entrada</th>
                            <th>Hora Salida</th>
                        </tr>
                    </thead>
                    <tbody>
                        {registros.slice(-10).map((registro) => (
                            <tr key={registro.NIT || registro.id}>
                                <td>{registro.persona_nombre}</td>
                                <td>{registro.fecha}</td>
                                <td>{registro.hora_entrada}</td>
                                <td>{registro.hora_salida || '-'}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* ✅ Mini vista solo con el último registro */}
            {miniVista.length > 0 && (
                <div className="mini-vista">
                    <h4>Último Registro</h4>
                    {miniVista.map((registro) => (
                        <div key={registro.id} className="registro-item">
                            <p><strong>Nombre:</strong> {registro.persona_nombre}</p>
                            <p><strong>Hora Entrada:</strong> {registro.hora_entrada}</p>
                            <p><strong>Hora Salida:</strong> {registro.hora_salida || '-'}</p>
                            <hr />
                        </div>
                    ))}
                </div>
            )}

                <button onClick={descargarAusenciasSemanales} className="download-button">
                    Descargar Reporte Semanales
                </button>

                <button onClick={descargarAusenciasHistorico} className="download-button">
                    Descargar Reporte Historico
                </button>

        </div>
    );
};

export default RegistroAsistencia;