


const express = require('express');
const cors = require('cors');
const axios = require('axios'); // Use axios for HTTP requests
const fs = require('fs');
const path = require('path');
const csv = require('csv-parser');

const app = express();
const port = 5000;

app.use(cors({ origin: '*' }));
app.use(express.json());

axios.get('https://jsonplaceholder.typicode.com/todos/1')
    .then(response => console.log(response.data))
    .catch(error => console.error('Error:', error));

    const https = require('https');

    app.post('/login', async (req, res) => {
        try {
            const response = await axios.post('https://127.0.0.1:9115/login', req.body, { 
                httpsAgent: new https.Agent({ rejectUnauthorized: false }) // ✅ Ignore SSL errors
            });
            res.json(response.data);
        } catch (error) {
            console.error("Login Error:", error.message);
            res.status(error.response?.status || 500).json(error.response?.data || { error: "Login failed" });
        }
    });
    

// ✅ Function to read CSV data
function readCsvData(filePath) {
    const results = [];
    return new Promise((resolve, reject) => {
        fs.createReadStream(filePath)
            .pipe(csv())
            .on('data', (data) => results.push(data))
            .on('end', () => resolve(results))
            .on('error', (err) => reject(err));
    });
}

// ✅ Serve the toll report with time period filtering
app.get('/toll_report', async (req, res) => {
    const { startDate, endDate } = req.query;

    try {
        const tollPasses = await readCsvData(path.join(__dirname, 'data', 'passes-sample.csv'));

        const filteredTollPasses = tollPasses.filter(pass => {
            const passTime = new Date(pass.time);
            const start = new Date(startDate);
            const end = new Date(endDate);
            return passTime >= start && passTime <= end;
        });

        res.json({ tollPasses: filteredTollPasses });
    } catch (error) {
        console.error("Error reading toll data:", error);
        res.status(500).json({ message: "Error fetching toll report data." });
    }
});

// ✅ Serve the tag report with time period filtering
app.get('/tag_report', async (req, res) => {
    const { startDate, endDate } = req.query;

    try {
        const tags = await readCsvData(path.join(__dirname, 'data', 'tollstations2024.csv'));

        const filteredTags = tags.filter(tag => {
            const tagTime = new Date(tag.time);
            const start = new Date(startDate);
            const end = new Date(endDate);
            return tagTime >= start && tagTime <= end;
        });

        res.json({ tags: filteredTags });
    } catch (error) {
        console.error("Error reading tag data:", error);
        res.status(500).json({ message: "Error fetching tag report data." });
    }
});

// ✅ Serve static files (Frontend HTML, CSS, JS)
app.use(express.static(path.join(__dirname, 'public')));

// ✅ Start the server once (Fix duplicate app.listen)
app.listen(port, () => {
    console.log(`Node.js server running on http://localhost:${port}`);
});
