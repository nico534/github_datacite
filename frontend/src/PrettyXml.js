import React from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { darcula } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Button, Snackbar} from "@mui/material";

const PrettyXMLDisplay = ({ xml }) => {
  const [copidAlert, setCopyAlert] = React.useState(false)
  const formatXML = (xmlString) => {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlString, "application/xml");
    const serializer = new XMLSerializer();
    return serializer.serializeToString(xmlDoc);
  };

  const downloadTxtFile = () => {
    const element = document.createElement("a");
    const file = new Blob([xml], {type: 'application/xml'});
    element.href = URL.createObjectURL(file);
    element.download = "metadata-schema.xml";
    document.body.appendChild(element); // Required for this to work in FireFox
    element.click();
  }

  const coppyToClipboard = () => {
    setCopyAlert(true);
    navigator.clipboard.writeText(xml)
  }

  return (
    <div>
      <div style={{alignSelf: "flex-end"}}>
        <Button onClick={event => downloadTxtFile()}>Download</Button>
        <Button onClick={event => coppyToClipboard()}>Coppy</Button>
        <Snackbar
          anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
          open={copidAlert}
          autoHideDuration={6000}
          onClose={() => setCopyAlert(false)}
          message="Coppied to clipboard"
        />
      </div>
      <div style={{width: "100%"}}>
        <SyntaxHighlighter language="xml" style={darcula}>
          {formatXML(xml)}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

export default PrettyXMLDisplay;