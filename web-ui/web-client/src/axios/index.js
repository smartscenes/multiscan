import axios from 'axios';

// API server url
axios.defaults.baseURL = require("/static/config.json").baseURL
// axios.defaults.baseURL = 'http://localhost:3030/'

axios.defaults.timeout = 50000;

export default axios;
