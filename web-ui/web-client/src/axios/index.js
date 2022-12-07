import axios from 'axios';

// API server url
axios.defaults.baseURL = 'http://spathi.cmpt.sfu.ca/multiscan/webui/'
// axios.defaults.baseURL = 'http://localhost:3030/'
axios.defaults.timeout = 50000;

export default axios;
