export const getLocations = async () => {
    try {
        const res = await fetch('http://127.0.0.1:8000/locations');
        const data = await res.json();
        return data;
    } catch (err) {
        console.error(err);
        return []; 
    }
};