import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    primary: {
      main: "#4f46e5",
      dark: "#111111",
      light: "#FFFFFF",
      
      
    },
    secondary: {
      main: "#06b6d4",
    },
    background: {
        default:  "#FFFFFF",

    },
    success: {
         main: '#0ED443' 
    },

   
  },
  typography: {
    fontFamily: "Inter, sans-serif",
    h3: {
        fontSize: '1.5rem'
    },
    h4: {
      fontSize: '1rem',
    },
    h5:{
        fontSize: '0.8rem',
    },
    body1: {
      fontSize: '1.2rem',
    },
  },
});