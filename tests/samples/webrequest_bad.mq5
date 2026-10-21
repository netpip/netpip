// Test sample: sends data to a remote server
void OnTick()
{
   char data[], result[];
   string headers;
   WebRequest("POST", "https://example.com/collect", "", 5000, data, result, headers);
}
