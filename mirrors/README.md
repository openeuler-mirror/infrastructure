## mirrors
The folder is built to store openEuler mirrors source info. Each yaml file named after the mirror name is responsible 
for managing the source information of the mirror.The table shows fields and descriptions below.
 
  | Field | Description |
  |  :---:  |  :---: |
  | Name | Name of the mirror |
  | HttpURL | HTTP base URL |
  | RsyncURL | RSYNC base URL (for scanning only) |
  | FtpURL | FTP base URL (for scanning only) |
  | SponsorName | Name of the sponsor |
  | SponsorURL | URL of the sponsor |
  | SponsorLogoURL | URL of a logo to display for this mirror, the image must be square and in jpg/png format |
  | AdminName | Admin's name |
  | AdminEmail | Admin's email |
  | ContinentOnly | The mirror should only handle its continent |
  | CountryOnly | The mirror should only handle its country-only |
  | ASOnly | The mirror should only handle clients in the same As number |
  | Score | Weight to give to the mirror during selection |
  | Enabled | Open or not |
  | AllowRedirects | Allow redirects |
