const fs = require('fs');
const content = fs.readFileSync('assests/js/weather.js', 'utf8');
try {
    new Function(content);
    console.log('Syntax OK');
} catch (e) {
    console.error(e);
}
