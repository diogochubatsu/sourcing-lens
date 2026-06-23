export function getOpenApiSpec(baseUrl = 'http://localhost:3002') {
  return {
    openapi: '3.1.0',
    info: {
      title: '1688 Intel API',
      version: '0.1.0',
      description: 'Standalone service for 1688 rankings and bestseller intelligence.',
    },
    servers: [{ url: baseUrl }],
    components: {
      securitySchemes: {
        ApiKeyAuth: {
          type: 'apiKey',
          in: 'header',
          name: 'X-API-Key',
        },
      },
    },
    security: [{ ApiKeyAuth: [] }],
    paths: {
      '/api/meta': {
        get: {
          summary: 'Service metadata',
          responses: { '200': { description: 'Metadata payload' } },
        },
      },
      '/api/rankings': {
        get: {
          summary: 'Latest or selected ranking run',
          parameters: [
            { name: 'run', in: 'query', schema: { type: 'string' } },
            { name: 'limit', in: 'query', schema: { type: 'integer' } },
            { name: 'min_repurchase', in: 'query', schema: { type: 'integer' } },
            { name: 'min_rebuy_rate', in: 'query', schema: { type: 'integer' }, deprecated: true },
          ],
          responses: { '200': { description: 'Ranking records' }, '401': { description: 'Unauthorized' } },
        },
      },
      '/api/rankings/runs': {
        get: {
          summary: 'Available ranking runs',
          responses: { '200': { description: 'Run list' }, '401': { description: 'Unauthorized' } },
        },
      },
      '/api/bestsellers': {
        get: {
          summary: 'Latest or selected bestseller run',
          parameters: [
            { name: 'run', in: 'query', schema: { type: 'string' } },
            { name: 'limit', in: 'query', schema: { type: 'integer' } },
            { name: 'keyword', in: 'query', schema: { type: 'string' } },
          ],
          responses: { '200': { description: 'Bestseller records' }, '401': { description: 'Unauthorized' } },
        },
      },
      '/api/bestsellers/runs': {
        get: {
          summary: 'Available bestseller runs',
          responses: { '200': { description: 'Run list' }, '401': { description: 'Unauthorized' } },
        },
      },
      '/api/pipeline/trigger': {
        post: {
          summary: 'Trigger a rankings or bestsellers script run',
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    target: { type: 'string', enum: ['rankings', 'bestsellers'] },
                  },
                  required: ['target'],
                },
              },
            },
          },
          responses: {
            '200': { description: 'Trigger accepted in non-production environments' },
            '401': { description: 'Unauthorized' },
            '501': { description: 'Not implemented in production' },
          },
        },
      },
    },
  };
}