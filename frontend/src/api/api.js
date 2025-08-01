const API_URL = "http://127.0.0.1:8000/registros/";

export const fetchRegistros = async () => {
    const response = await fetch(API_URL);
    if (!response.ok) {
        throw new Error("Error al cargar los registros");
    }
    return response.json();
};