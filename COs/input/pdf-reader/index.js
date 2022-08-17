const axios = require('axios');
const fs = require('fs');

if (!process.argv || process.argv.length < 5) {
  console.log("Please supply 3 arguments (url, file name, folder to download to");
  process.exit(1);
}

const [_, __, url, fileName, downloadTo] = process.argv || ['', '', ''];

axios({
  url,
  responseType: 'arraybuffer',
}).then((response) => {
  try {
    if (!fs.existsSync(`${downloadTo || __dirname}/${fileName}.pdf`)) {
      fs.writeFileSync(`${downloadTo || __dirname}/${fileName}.pdf`, response.data);
    } else {
      for (let i = 0; i < 1000; i++) {
        if (!fs.existsSync(`${downloadTo || __dirname}/${fileName}-${i}.pdf`)) {
          fs.writeFileSync(`${downloadTo || __dirname}/${fileName}-${i}.pdf`, response.data);
          break;
        }
      }
    }
  } catch (err) {
    console.error(err);
  }
 });

