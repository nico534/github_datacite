import React from 'react'
import PrettyXMLDisplay from './PrettyXml'
import { Button, Box, TextField, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import Grid from '@mui/material/Grid2';
import env from "react-dotenv";

export default function App() {
  const [options, setOptions] = React.useState({
    owner: "",
    project: "",
    apiToken: ""
  })
  const [xml, setXml] = React.useState('<hello attr="World" />')
  const [waiting, setWaiting] = React.useState(false)
  const [error, setError] = React.useState({
    open: false,
    message: "",
    status: 200
  })
  const onClickEvent = () => {
    console.log("Click event!")
    setTimeout(() => setWaiting(true), 0)
    const requestOptions = {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options)
    };
    fetch(`${env.API_URL}/generate`, requestOptions)
        .then(response => response.text().then(data => {
            setTimeout(() => setWaiting(false), 0);
            if (response.status > 201) {
              setError({message: data, status: response.status, open: true});
            } else {
              console.log(data);
              setXml(data);
            }
        })).catch(e => {
          console.log(e)
          setTimeout(() => setWaiting(false), 0)
        });
  }
  return (
    <div style={{display: "flex", alignItems: "center", justifyContent: "center"}}>
      <div style={{maxWidth: "1200px", padding: "15px"}}>
        <Box sx={{ flexGrow: 1 }} >
          <Grid container spacing={2} >
            <Grid size={12} style={{padding: "10px", display: "flex", alignItems: "center", justifyContent: "space-between"}}>
              <TextField onChange={newVal => setOptions({...options, owner: newVal.target.value})} id="standard-basic" label="Owner" variant="standard" />
              <TextField onChange={newVal => setOptions({...options, project: newVal.target.value})} id="standard-basic" label="Project" variant="standard" />
              <TextField onChange={newVal => setOptions({...options, apiToken: newVal.target.value})} id="standard-basic" label="API-Token (not mandatory)" variant="standard" />
              <Button disabled={waiting} onClick={event => onClickEvent()}>Execute</Button><br/>
            </Grid>
            <Grid size={12}>
              {waiting && <LinearProgress />}
              <div >
                <PrettyXMLDisplay xml={xml} />
              </div>
            </Grid>
          </Grid>
        </Box>
        <Dialog 
          open={error.open}
          onClose={() => setError({...error, open:false})}
          >
            <DialogTitle>
              Error: Request return StatusCode {error.status}
            </DialogTitle>
            <DialogContent>
              { error.message }
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setError({...error, open: false})}>Close</Button>
            </DialogActions>
        </Dialog>
      </div>
    </div>
  )
}


// import './App.css';
// import XMLViewer from 'react-xml-viewer'
// import React, { useEffect, useState } from "react";
// 
// function App() {
//   let [xml, setXml] = useState("")
// 
//   let handleClick = () => {
//       fetch('/example.xml')
//       .then((r) => r.text())
//       .then(text  => {
//         console.log(text);
//         setXml(text)
//       })  
//     } 
//     
//   return (
//     <div className="App">
//         <button onClick={handleClick} >Get XML</button>
//         <div>
//           <XMLViewer xml={xml} />
//         </div>
//     </div>
//   );
// }
// 
// export default App;
// 